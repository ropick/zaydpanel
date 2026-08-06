#!/usr/bin/env python3
"""FASE 3: Install aaPanel - fix: needs sudo"""
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
print("FASE 3: Install aaPanel (with sudo)")
print("=" * 60)

client = connect()

# Kill any existing install
print("\n[1] Kill any existing install process...")
run(client, "sudo pkill -f 'aapanel_install' 2>/dev/null; sleep 1")

# Make sure nginx/certbot stopped
print("\n[2] Stop Docker nginx/certbot...")
run(client, "docker stop nusahost-nginx nusahost-certbot 2>&1")

# Re-download with sudo
print("\n[3] Download aaPanel installer...")
out, err, code = run(client, "sudo curl -sSL -o /www/aapanel_install.sh https://www.aapanel.com/script/install_6.0_en.sh 2>&1 && sudo ls -la /www/aapanel_install.sh", timeout=60)
print(f"  Download: {out}")

# Verify file
out, _, _ = run(client, "sudo head -3 /www/aapanel_install.sh")
print(f"  First 3 lines: {out}")
if "aapanel" not in out.lower() and "#!" not in out:
    print("  ❌ File looks invalid, trying alternate URL...")
    run(client, "sudo curl -sSL -o /www/aapanel_install.sh http://www.aapanel.com/script/install_6.0_en.sh 2>&1", timeout=60)

# Make executable
run(client, "sudo chmod +x /www/aapanel_install.sh", timeout=10)

# Install with sudo, pipe "y" to confirm /www directory
print("\n[4] Installing aaPanel (with sudo)...")
print("  ⏳ This takes 10-20 min on ARM64...")

# Create install wrapper that uses sudo
install_wrapper = r"""cat > /tmp/run_install.sh << 'EOFILE'
#!/bin/bash
# Pipe "y" to accept /www directory prompt, use sudo
echo "y" | sudo bash /www/aapanel_install.sh > /tmp/aapanel_install.log 2>&1
echo ""
echo "=== DONE_EXIT=$? ==="
EOFILE
chmod +x /tmp/run_install.sh"""
run(client, install_wrapper, timeout=10)

# Run in background
run(client, "nohup /tmp/run_install.sh &", timeout=10)
time.sleep(5)

# Check it started
out, _, _ = run(client, "ps aux | grep 'aapanel' | grep -v grep")
print(f"  Running: {'YES ✅' if out else 'NO ❌'}")
if out:
    for line in out.split('\n')[:3]:
        print(f"    {line.strip()[:100]}")

# Monitor every 30s
print("\n[5] Monitoring...")
for i in range(60):  # 30 minutes max
    time.sleep(30)
    
    running, _, _ = run(client, "ps aux | grep 'aapanel' | grep -v grep")
    log, _, _ = run(client, "tail -3 /tmp/aapanel_install.log 2>/dev/null")
    elapsed = (i + 1) * 30
    
    status = "🔄 RUNNING" if running else "🏁 ENDED"
    print(f"  [{elapsed}s] {status}")
    if log:
        for line in log.split('\n'):
            c = line.strip()[:120]
            if c:
                print(f"    {c}")
    
    # Check completion
    out_done, _, _ = run(client, "grep -c 'DONE_EXIT' /tmp/aapanel_install.log 2>/dev/null")
    out_bt, _, _ = run(client, "sudo which bt 2>/dev/null")
    
    if out_bt or (out_done and int(out_done.strip() or '0') > 0):
        print("\n  🎉 Installation finished!")
        time.sleep(3)
        
        # Show credentials
        log_full, _, _ = run(client, "tail -50 /tmp/aapanel_install.log 2>/dev/null")
        for line in log_full.split('\n'):
            if any(k in line.lower() for k in ['congratulat', 'panel', 'username', 'password', 'url', 'http://', 'https://', '====', 'bt default', 'in the browser']):
                print(f"  {line.strip()}")
        
        out_bt_def, _, _ = run(client, "sudo bt default 2>/dev/null")
        if out_bt_def:
            print(f"\n  ── Panel Credentials ──")
            for line in out_bt_def.split('\n'):
                print(f"  {line}")
        
        break
    
    if not running:
        print("  ⚠️ Process ended early. Checking...")
        log_end, _, _ = run(client, "tail -30 /tmp/aapanel_install.log 2>/dev/null")
        print(log_end)
        # Check if there's an error about root
        if "root" in log_end.lower() or "non-root" in log_end.lower():
            print("\n  🔧 Trying direct sudo install...")
            run(client, "nohup bash -c 'echo y | sudo bash /www/aapanel_install.sh' > /tmp/aapanel_install2.log 2>&1 &", timeout=10)
            time.sleep(5)
            out2, _, _ = run(client, "ps aux | grep 'aapanel' | grep -v grep")
            if out2:
                print("  ✅ Re-launched with sudo!")
                # Continue monitoring
                continue
            else:
                break
        break

# Final check
print("\n[6] Final status check...")
out, _, _ = run(client, "sudo which bt 2>/dev/null")
print(f"  bt command: {'FOUND ✅' if out else 'NOT FOUND ❌'}")

out, _, _ = run(client, "ss -tlnp 2>/dev/null | grep -E ':(80|443|8888|3306|21) '")
print(f"  Ports:\n{out}" if out else "  Ports: None key ports")

out, _, _ = run(client, "curl -sI http://localhost:8888 2>/dev/null | head -3")
print(f"  Panel (8888): {out.strip() if out else 'N/A'}")

out, _, _ = run(client, "docker ps --format '{{.Names}} {{.Status}}'")
print(f"  Docker: {out if out else 'No containers'}")

out, _, _ = run(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null")
print(f"  Next.js app (3000): HTTP {out}")

client.close()
print("\n" + "=" * 60)
