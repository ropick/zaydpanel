#!/usr/bin/env python3
"""
FASE 3: Install aaPanel - Open Source Control Panel
1. Stop Docker nginx/certbot (keep app on 3000)
2. Install aaPanel
3. Will configure reverse proxy after installation
"""
import paramiko, time, sys

def connect():
    key = paramiko.RSAKey.from_private_key_file("/home/z/my-project/deploy/nusahost_id")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=120, sudo=False):
    if sudo:
        cmd = f"sudo {cmd}"
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

print("=" * 60)
print("FASE 3: Install aaPanel - Open Source Control Panel")
print("=" * 60)

client = connect()

# === STEP 1: Stop Docker nginx + certbot, keep app on port 3000 ===
print("\n[STEP 1] Stop Docker nginx/certbot (keep app on 3000)...")
out, err, code = run(client, "cd /opt/nusahost/deploy && docker compose stop nginx certbot", timeout=60)
print(f"  Stop nginx+certbot: exit={code}")
print(f"  stdout: {out}" if out else "")
print(f"  stderr: {err}" if err else "")

# Verify app is still running
out, err, code = run(client, "docker ps --format '{{.Names}} {{.Status}}' | grep nusahost")
print(f"  Running containers:\n    {out}")

# Check port 80 is free
out, err, code = run(client, "ss -tlnp | grep ':80 '")
if not out:
    print("  Port 80: FREE ✅")
else:
    print(f"  Port 80 still in use: {out}")
    # Force stop nginx container
    run(client, "docker stop nusahost-nginx 2>/dev/null")
    time.sleep(2)
    out2, _, _ = run(client, "ss -tlnp | grep ':80 '")
    if not out2:
        print("  Port 80: Now FREE ✅")

# Check port 443 is free
out, err, code = run(client, "ss -tlnp | grep ':443 '")
if not out:
    print("  Port 443: FREE ✅")
else:
    print(f"  Port 443 still in use: {out}")

# === STEP 2: Prepare system for aaPanel ===
print("\n[STEP 2] Prepare system for aaPanel...")

# Check OS
out, _, _ = run(client, "cat /etc/os-release | head -4")
print(f"  OS: {out}")

# Install required dependencies
print("  Installing dependencies...")
out, err, code = run(client, "apt-get update -y 2>&1 | tail -5", timeout=120, sudo=True)
print(f"  apt update: exit={code}")

out, err, code = run(client, "apt-get install -y curl wget python3 python3-pip libwww-perl 2>&1 | tail -5", timeout=180, sudo=True)
print(f"  Install deps: exit={code}")

# === STEP 3: Download aaPanel installer ===
print("\n[STEP 3] Download aaPanel installer...")
out, err, code = run(client, "cd /tmp && curl -sSO https://www.aapanel.com/script/install_6.0_en.sh && ls -la install_6.0_en.sh", timeout=60, sudo=True)
print(f"  Download: exit={code}")
if "install_6.0_en.sh" in out:
    print("  Installer downloaded ✅")
else:
    print(f"  Download failed: {err}")

# === STEP 4: Install aaPanel (non-interactive) ===
print("\n[STEP 4] Installing aaPanel...")
print("  ⏳ This will take 10-15 minutes...")

# Write the install command to a script that auto-answers "y"
cmd_script = """cat > /tmp/install_aapanel.sh << 'EOFILE'
#!/bin/bash
cd /tmp
echo "y" | bash install_6.0_en.sh 2>&1
echo "INSTALL_EXIT_CODE=$?"
EOFILE
chmod +x /tmp/install_aapanel.sh
"""
run(client, cmd_script, timeout=10, sudo=True)

# Run installation in background with nohup
run(client, "nohup bash /tmp/install_aapanel.sh > /tmp/aapanel_install.log 2>&1 &", timeout=10, sudo=True)
print("  Installation started in background...")

# Monitor installation progress
print("\n[STEP 5] Monitoring installation...")
for i in range(90):  # Check every 20s for up to 30 minutes
    time.sleep(20)
    
    # Check if still running
    out, _, _ = run(client, "ps aux | grep 'install_6.0' | grep -v grep")
    still_running = bool(out)
    
    # Get last lines of log
    log, _, _ = run(client, "tail -5 /tmp/aapanel_install.log 2>/dev/null")
    
    print(f"  [{i*20}s] Running: {'YES' if still_running else 'NO'}")
    if log:
        for line in log.split('\n')[-2:]:
            print(f"         {line.strip()[:100]}")
    
    # Check if install completed
    out2, _, _ = run(client, "grep -c 'Congratulations' /tmp/aapanel_install.log 2>/dev/null")
    if out2 and int(out2) > 0:
        print("\n  🎉 aaPanel installation completed!")
        break
    
    if not still_running:
        # Check exit code
        out3, _, _ = run(client, "grep 'INSTALL_EXIT_CODE' /tmp/aapanel_install.log 2>/dev/null")
        out4, _, _ = run(client, "tail -20 /tmp/aapanel_install.log 2>/dev/null")
        print(f"\n  Install process ended. Exit check: {out3}")
        print(f"  Last log:\n{out4}")
        # Check if bt command exists
        out5, _, _ = run(client, "which bt 2>/dev/null")
        if out5:
            print("  🎉 aaPanel installed successfully (bt command found)!")
            break
        else:
            print("  ❌ Installation may have failed. Check logs.")
            break

# === STEP 6: Get aaPanel login info ===
print("\n[STEP 6] Retrieving aaPanel credentials...")
log_full, _, _ = run(client, "cat /tmp/aapanel_install.log 2>/dev/null")

# Extract panel URL, username, password
panel_info = []
for line in log_full.split('\n'):
    if any(kw in line.lower() for kw in ['congratulations', 'panel', 'username', 'password', 'http://', 'https://', 'bt default', 'url']):
        panel_info.append(line.strip())

if panel_info:
    print("  Panel info from log:")
    for info in panel_info:
        print(f"    {info}")

# Also try bt default
out, err, code = run(client, "bt default 2>/dev/null", timeout=15, sudo=True)
if out:
    print("  bt default output:")
    print(f"    {out}")

# Check aaPanel status
out, _, _ = run(client, "bt status 2>/dev/null", timeout=15, sudo=True)
if out:
    print(f"\n  aaPanel status:\n    {out}")

# Check what's listening on ports
print("\n[STEP 7] Port status after aaPanel install:")
out, _, _ = run(client, "ss -tlnp | grep -E ':(80|443|8888|3306|21|22) '")
print(f"  {out if out else 'No key ports found'}")

# Check if Nginx was installed by aaPanel
out, _, _ = run(client, "which nginx && nginx -v 2>&1", sudo=True)
print(f"  Nginx: {out}")

# Check Docker app still running
out, _, _ = run(client, "docker ps --format '{{.Names}} {{.Status}}' | grep nusahost")
print(f"  Docker containers:\n    {out if out else 'No nusahost containers running'}")

out, _, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000 2>/dev/null")
print(f"  App on port 3000: HTTP {out}")

client.close()

print("\n" + "=" * 60)
print("FASE 3 COMPLETE")
print("=" * 60)
print("\nNext: Configure aaPanel reverse proxy for staging.pro99.my.id → port 3000")
