#!/usr/bin/env python3
"""FASE 3: Install aaPanel - step by step with proper sudo handling"""
import paramiko, time

def connect():
    key = paramiko.RSAKey.from_private_key_file("/home/z/my-project/deploy/nusahost_id")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

client = connect()

# Kill old processes
run(client, "sudo pkill -f 'aapanel' 2>/dev/null; sudo pkill -f 'install_6' 2>/dev/null")
time.sleep(2)

# Stop Docker nginx/certbot
print("Stopping Docker nginx/certbot...")
run(client, "docker stop nusahost-nginx nusahost-certbot 2>/dev/null")
time.sleep(3)

# Check ports free
out, _, _ = run(client, "ss -tlnp | grep -E ':(80|443) '")
print(f"Ports 80/443: {'FREE' if not out else out}")

# Download installer
print("Downloading installer...")
run(client, "sudo rm -f /tmp/aapanel_install.sh 2>/dev/null", timeout=10)
out, err, code = run(client, "sudo curl -sSL -o /tmp/aapanel_install.sh https://www.aapanel.com/script/install_6.0_en.sh 2>&1", timeout=60)
print(f"curl: code={code}, {err if err else 'OK'}")

# Check file exists and is valid
out, _, _ = run(client, "sudo ls -la /tmp/aapanel_install.sh 2>&1")
print(f"File: {out}")

out, _, _ = run(client, "sudo head -5 /tmp/aapanel_install.sh 2>&1")
print(f"Content: {out[:200]}")

# Make executable
run(client, "sudo chmod +x /tmp/aapanel_install.sh", timeout=10)

# Run with sudo, auto-answer "y"
print("\nStarting installation (auto-answered 'y')...")
# Use nohup + sudo to run in background
run(client, 'nohup sudo bash -c "echo y | bash /tmp/aapanel_install.sh" > /tmp/aapanel_install.log 2>&1 &', timeout=10)
time.sleep(8)

# Check
out, _, _ = run(client, "ps aux | grep 'install' | grep -v grep")
print(f"Process: {out[:200] if out else 'NONE'}")

log, _, _ = run(client, "tail -5 /tmp/aapanel_install.log 2>/dev/null")
print(f"Log start:\n{log}")

client.close()
print("\nInstall launched. Run check_aapanel.py to monitor progress.")
