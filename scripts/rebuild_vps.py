import paramiko, time

def connect():
    key = paramiko.RSAKey.from_private_key_file("/home/z/my-project/deploy/nusahost_id")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

client = connect()
print("SSH Connected\n")

# 1. Upload fixed Dockerfile
print("[1/3] Upload fixed Dockerfile...")
sftp = client.open_sftp()
sftp.put("/home/z/my-project/deploy/Dockerfile", "/opt/nusahost/deploy/Dockerfile")
sftp.close()
print("  Done")

# 2. Rebuild in background
print("\n[2/3] Rebuild (npm instead of bun)...")
script = """#!/bin/bash
cd /opt/nusahost
echo "[$(date)] REBUILD START" > /tmp/nusahost.log
sudo docker compose -f deploy/docker-compose.yml build --no-cache >> /tmp/nusahost.log 2>&1
echo "[$(date)] BUILD EXIT: $?" >> /tmp/nusahost.log
sudo docker compose -f deploy/docker-compose.yml up -d >> /tmp/nusahost.log 2>&1
echo "[$(date)] UP EXIT: $?" >> /tmp/nusahost.log
sudo docker compose -f deploy/docker-compose.yml ps >> /tmp/nusahost.log 2>&1
echo "[$(date)] FINISHED" >> /tmp/nusahost.log
"""
run(client, f"echo '{script}' > /opt/nusahost/rebuild.sh && chmod +x /opt/nusahost/rebuild.sh")
run(client, "nohup bash /opt/nusahost/rebuild.sh &>/dev/null &")
print("  Building in background...")

# 3. Wait and check
time.sleep(5)
out, _, _ = run(client, "tail -5 /tmp/nusahost.log")
print(f"\n[3/3] Initial progress:\n{out}")

client.close()
print("\nBuild running. Will check progress in ~3 minutes.")
