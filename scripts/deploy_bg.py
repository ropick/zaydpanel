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

def run(client, cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

def stream(client, cmd, timeout=300):
    channel = client.get_transport().open_session()
    channel.settimeout(timeout)
    channel.get_pty()
    channel.exec_command(cmd)
    output = ""
    while True:
        if channel.recv_ready():
            d = channel.recv(4096).decode(); output += d; print(d, end='', flush=True)
        if channel.recv_stderr_ready():
            d = channel.recv_stderr(4096).decode(); output += d; print(d, end='', flush=True)
        if channel.exit_status_ready():
            while channel.recv_ready(): output += channel.recv(4096).decode()
            break
        time.sleep(0.1)
    return output, channel.recv_exit_status()

client = connect()
print("SSH Connected\n")

# Open ports
print("[1/2] Firewall...")
stream(client, """
sudo iptables -I INPUT -m state --state NEW -p tcp --dport 80 -j ACCEPT 2>/dev/null
sudo iptables -I INPUT -m state --state NEW -p tcp --dport 443 -j ACCEPT 2>/dev/null
echo "Done"
""", timeout=30)
print()

# Run build + start as background script on VPS
print("[2/2] Build & Start (running on VPS, non-blocking)...")
# Write a deploy script on the VPS, then execute it with nohup

deploy_script = f"""#!/bin/bash
cd {REMOTE_DIR}
echo "[$(date)] Starting build..." > /tmp/nusahost-deploy.log

# Build
sudo docker compose -f deploy/docker-compose.yml build --no-cache >> /tmp/nusahost-deploy.log 2>&1
BUILD_CODE=$?
echo "[$(date)] Build done (code=$BUILD_CODE)" >> /tmp/nusahost-deploy.log

# Start
sudo docker compose -f deploy/docker-compose.yml up -d >> /tmp/nusahost-deploy.log 2>&1
START_CODE=$?
echo "[$(date)] Start done (code=$START_CODE)" >> /tmp/nusahost-deploy.log

# Status
sudo docker compose -f deploy/docker-compose.yml ps >> /tmp/nusahost-deploy.log 2>&1
echo "[$(date)] ALL DONE" >> /tmp/nusahost-deploy.log
"""

# Upload script to VPS
sftp = client.open_sftp()
with sftp.file(f"{REMOTE_DIR}/deploy_now.sh", 'w') as f:
    f.write(deploy_script)
sftp.chmod(f"{REMOTE_DIR}/deploy_now.sh", 0o755)
sftp.close()

# Run in background
run(client, f"cd {REMOTE_DIR} && nohup bash deploy_now.sh > /tmp/nusahost-deploy-stdout.log 2>&1 &")

print("  Deploy running in background on VPS!")
print("  Monitor: ssh opc@168.110.210.148 'tail -f /tmp/nusahost-deploy.log'")

# Wait a bit and show initial progress
time.sleep(5)
out, err, code = run(client, "cat /tmp/nusahost-deploy.log 2>/dev/null || echo 'Log not ready yet'")
print(f"\n  Initial log:\n{out}")

client.close()
print("\nDeploy is running. Check status in 2-3 minutes.")
