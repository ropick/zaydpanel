import paramiko
import sys
import time

VPS_IP = "168.110.210.148"
VPS_USER = "opc"
KEY_PATH = "/home/z/my-project/deploy/nusahost_id"
REMOTE_DIR = "/opt/nusahost"

def connect():
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(VPS_IP, username=VPS_USER, pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

client = connect()

# Open ports
print("Opening ports...")
run(client, "sudo iptables -I INPUT -m state --state NEW -p tcp --dport 80 -j ACCEPT")
run(client, "sudo iptables -I INPUT -m state --state NEW -p tcp --dport 443 -j ACCEPT")
print("Ports opened")

# Upload deploy script
sftp = client.open_sftp()
script = f"""#!/bin/bash
cd {REMOTE_DIR}
echo "[$(date)] BUILD START" > /tmp/nusahost.log
sudo docker compose -f deploy/docker-compose.yml build --no-cache >> /tmp/nusahost.log 2>&1
echo "[$(date)] BUILD DONE: $?" >> /tmp/nusahost.log
sudo docker compose -f deploy/docker-compose.yml up -d >> /tmp/nusahost.log 2>&1
echo "[$(date)] UP DONE: $?" >> /tmp/nusahost.log
sudo docker compose -f deploy/docker-compose.yml ps >> /tmp/nusahost.log 2>&1
echo "[$(date)] FINISHED" >> /tmp/nusahost.log
"""
with sftp.file(f"{REMOTE_DIR}/go.sh", 'w') as f: f.write(script)
sftp.chmod(f"{REMOTE_DIR}/go.sh", 0o755)
sftp.close()
print("Script uploaded")

# Launch in background
run(client, f"nohup bash {REMOTE_DIR}/go.sh &>/tmp/nusahost-out.log &")
print("Deploy started in background")

time.sleep(3)
out, _, _ = run(client, "cat /tmp/nusahost.log 2>/dev/null")
print(f"Log: {out if out else '(building...)'}")

client.close()
print("OK - check VPS for progress")
