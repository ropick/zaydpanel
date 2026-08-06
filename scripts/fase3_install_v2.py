#!/usr/bin/env python3
"""FASE 3: Install aaPanel - retry with direct download"""
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

print("=" * 60)
print("FASE 3: Install aaPanel (retry)")
print("=" * 60)

client = connect()

# Step 1: Make sure Docker nginx/certbot are stopped
print("\n[1] Stop Docker nginx/certbot to free port 80/443...")
out, err, code = run(client, "docker stop nusahost-nginx nusahost-certbot 2>&1")
print(f"    Stop: {out}")
out, err, code = run(client, "ss -tlnp | grep -E ':(80|443) '")
print(f"    Ports 80/443: {'FREE' if not out else out}")

# Step 2: Download installer
print("\n[2] Download aaPanel installer...")

# Try multiple URLs
urls = [
    "https://www.aapanel.com/script/install_6.0_en.sh",
    "https://www.aapanel.com/script/install.sh",
    "http://www.aapanel.com/script/install_6.0_en.sh",
]

for url in urls:
    print(f"  Trying: {url}")
    out, err, code = run(client, f"curl -sSL -o /tmp/aapanel_install.sh '{url}' && echo 'OK' && ls -la /tmp/aapanel_install.sh", timeout=60)
    print(f"    Result: code={code}, {out}")
    if code == 0 and "aapanel_install.sh" in out:
        # Verify file is valid (not 404 page)
        out2, _, _ = run(client, "head -5 /tmp/aapanel_install.sh")
        if "aapanel" in out2.lower() or "install" in out2.lower() or "#!" in out2:
            print(f"    First lines: {out2}")
            print("    ✅ Download successful!")
            break
        else:
            print(f"    ❌ Invalid file (not a script): {out2}")
    else:
        print(f"    ❌ Failed: {err}")

# Step 3: Install
print("\n[3] Starting aaPanel installation...")
print("  ⏳ This will take 10-20 minutes on ARM64...")

# Make executable
run(client, "chmod +x /tmp/aapanel_install.sh", timeout=10)

# Install in background with auto-answer
install_cmd = """cat > /tmp/run_aapanel_install.sh << 'EOFILE'
#!/bin/bash
echo "" | bash /tmp/aapanel_install.sh > /tmp/aapanel_install.log 2>&1
echo ""
echo "=== INSTALL_FINISHED_EXIT=$? ==="
EOFILE
chmod +x /tmp/run_aapanel_install.sh"""
run(client, install_cmd, timeout=10)

# Start in background
run(client, "nohup /tmp/run_aapanel_install.sh > /tmp/aapanel_bg.log 2>&1 &", timeout=10)

time.sleep(5)

# Confirm it started
out, _, _ = run(client, "ps aux | grep 'aapanel' | grep -v grep")
print(f"  Install process: {'RUNNING' if out else 'NOT RUNNING'}")
if out:
    print(f"  {out}")

# Monitor
print("\n[4] Monitoring installation (checking every 30s)...")
for i in range(60):  # Up to 30 minutes
    time.sleep(30)
    
    running, _, _ = run(client, "ps aux | grep -E 'aapanel|install' | grep -v grep")
    log, _, _ = run(client, "tail -3 /tmp/aapanel_install.log 2>/dev/null")
    
    elapsed = (i + 1) * 30
    status = "RUNNING" if running else "ENDED"
    print(f"  [{elapsed}s] {status}")
    if log:
        for line in log.split('\n'):
            clean = line.strip()[:120]
            if clean:
                print(f"         {clean}")
    
    # Check if done
    out_done, _, _ = run(client, "grep -c 'INSTALL_FINISHED' /tmp/aapanel_install.log 2>/dev/null")
    out_bt, _, _ = run(client, "which bt 2>/dev/null")
    
    if out_bt or (out_done and int(out_done) > 0):
        print("\n  🎉 aaPanel installation finished!")
        
        # Get final info
        time.sleep(3)
        log_full, _, _ = run(client, "tail -50 /tmp/aapanel_install.log 2>/dev/null")
        for line in log_full.split('\n'):
            if any(k in line.lower() for k in ['congratulat', 'panel', 'username', 'password', 'url', 'http', '================================================================']):
                print(f"  {line.strip()}")
        
        # bt default
        out_bt_def, _, _ = run(client, "bt default 2>/dev/null")
        if out_bt_def:
            print(f"\n  bt default:\n{out_bt_def}")
        
        break
    
    if not running:
        print("  Process ended but no bt command found. Checking logs...")
        log_end, _, _ = run(client, "tail -50 /tmp/aapanel_install.log 2>/dev/null")
        print(log_end)
        break

# Final status check
print("\n[5] Final status...")
out, _, _ = run(client, "which bt 2>/dev/null && echo 'aaPanel INSTALLED' || echo 'aaPanel NOT FOUND'")
print(f"  {out}")

out, _, _ = run(client, "ss -tlnp | grep -E ':(80|443|8888|3306) '")
print(f"  Ports: {out if out else 'None'}")

out, _, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:80 2>/dev/null")
print(f"  Port 80: HTTP {out}")

out, _, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:8888 2>/dev/null")
print(f"  Port 8888 (panel): HTTP {out}")

out, _, _ = run(client, "docker ps --format '{{.Names}} {{.Status}}'")
print(f"  Docker: {out if out else 'No containers'}")

out, _, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000 2>/dev/null")
print(f"  App (3000): HTTP {out}")

client.close()
print("\n" + "=" * 60)
print("DONE")
