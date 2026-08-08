#!/usr/bin/env python3
"""Diagnose aaPanel loading issue - likely CDN/static assets problem"""
import paramiko, time

def connect():
    key = paramiko.RSAKey.from_private_key_file("/home/z/my-project/deploy/nusahost_id")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=15):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

client = connect()

# 1. Check if CDN URL is configured (this often causes loading issues)
print("[1] Check CDN configuration...")
out, err, code = run(client, "sudo cat /www/server/panel/data/cdn_url.pl 2>&1")
print(f"  CDN URL: {out if out else 'NOT SET'}")

# 2. Check static files exist
print("\n[2] Check static files...")
out, err, code = run(client, "sudo ls /www/server/panel/BTPanel/static/ 2>&1 | head -10")
print(f"  Static dir: {out}")

out, err, code = run(client, "sudo ls /www/server/panel/BTPanel/static/vite/ 2>&1 | head -10")
print(f"  Vite dir: {out}")

# 3. Check if debug mode is on (uses local static instead of CDN)
print("\n[3] Debug mode...")
out, err, code = run(client, "sudo test -f /www/server/panel/data/debug.pl && echo 'ON' || echo 'OFF'")
print(f"  Debug: {out}")

# 4. Enable debug mode to force local static files (fixes CDN loading issues)
print("\n[4] Enable debug mode (force local static files)...")
out, err, code = run(client, "sudo touch /www/server/panel/data/debug.pl")
print(f"  Debug enabled: code={code}")

# 5. Set CDN to empty to use local files
print("\n[5] Disable CDN...")
out, err, code = run(client, "echo '' | sudo tee /www/server/panel/data/cdn_url.pl")
print(f"  CDN disabled: {out.strip()}")

# 6. Restart aaPanel
print("\n[6] Restart aaPanel...")
out, err, code = run(client, "sudo bt restart 2>&1")
print(f"  Restart: {out if out else 'done'}")
time.sleep(3)

# 7. Test if static files load
print("\n[7] Test static file access...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/static/vite/favicon.ico' --connect-timeout 5 -o /dev/null -w '%{http_code} %{size_download}' 2>&1")
print(f"  favicon.ico: {out}")

out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/static/vite/js/view-login.js' --connect-timeout 5 -o /dev/null -w '%{http_code} %{size_download}' 2>&1")
print(f"  login.js: {out}")

out, err, code = run(client, "sudo ls /www/server/panel/BTPanel/static/vite/js/ 2>&1 | head -10")
print(f"  JS files: {out}")

# 8. Check what the login page HTML references
print("\n[8] Check login page asset references...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -oE '(src|href)=\"[^\"]*\"' | head -15")
print(f"  Assets: {out}")

# 9. Check js_random
print("\n[9] JS random...")
out, err, code = run(client, "sudo cat /www/server/panel/data/js_random.pl 2>&1")
print(f"  js_random: {out if out else 'NOT SET'}")

client.close()
print("\n" + "=" * 60)
print("FIX: Debug mode enabled, CDN disabled")
print("Try accessing again - page should load from local static files")
print("=" * 60)
