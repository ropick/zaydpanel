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

def stream(client, cmd, timeout=600):
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

# Step 1: Open ports
print("[1/3] Open firewall ports...")
stream(client, """
sudo iptables -I INPUT -m state --state NEW -p tcp --dport 80 -j ACCEPT 2>/dev/null
sudo iptables -I INPUT -m state --state NEW -p tcp --dport 443 -j ACCEPT 2>/dev/null
sudo iptables -I INPUT -m state --state NEW -p tcp --dport 3000 -j ACCEPT 2>/dev/null
echo "Ports opened"
""", timeout=30)
print()

# Step 2: Build Docker
print("[2/3] Building Docker image (ARM64)...")
print("This takes 3-5 minutes on first build...\n")
out, ec = stream(client, f"cd {REMOTE_DIR} && sudo docker compose -f deploy/docker-compose.yml build --no-cache 2>&1", timeout=600)
print(f"\n  Build exit code: {ec}\n")

# Step 3: Start
print("[3/3] Starting containers...\n")
out, ec = stream(client, f"cd {REMOTE_DIR} && sudo docker compose -f deploy/docker-compose.yml up -d 2>&1", timeout=120)
print(f"\n  Start exit code: {ec}\n")

# Verify
print("--- Container Status ---")
out, err, code = run(client, f"cd {REMOTE_DIR} && sudo docker compose -f deploy/docker-compose.yml ps 2>&1")
print(out)
if err: print(f"stderr: {err}")

time.sleep(3)
print("\n--- Health Check ---")
out, err, code = run(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null")
print(f"  App (port 3000): HTTP {out}")
out, err, code = run(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:80 2>/dev/null")
print(f"  Nginx (port 80): HTTP {out}")

client.close()
print("\n" + "="*50)
print("  DEPLOY COMPLETE!")
print("  URL: http://168.110.210.148")
print("="*50)
