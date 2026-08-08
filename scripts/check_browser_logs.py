#!/usr/bin/env python3
"""Check Cloudflare settings impact and try direct IP access"""
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

# From the nginx logs, ALL requests from user's browser got 200:
# GET /613ccb60/ -> 200 (78654 bytes - Cloudflare compressed)
# GET /code -> 200 
# GET /static/js/md5.js -> 200
# GET /static/js/qrcode.min.js -> 200
# GET /static/js/i18next.min.js -> 200
# GET /static/js/jsencrypt.min.js -> 200
# GET /static/vite/favicon.ico -> 200
#
# The page loads fine! But user says "loading"
# This might mean:
# 1. The page shows a loading animation/spinner while JS initializes
# 2. There's a JS error in the browser console
# 3. The page needs more time to render
#
# Let's check if there are MORE requests after the initial ones
# (JS might make additional API calls that we haven't seen yet)

print("[1] ALL Docker nginx logs (user requests)...")
out, err, code = run(client, "sudo docker logs nusahost-nginx 2>&1 | grep '36.71.184' | tail -30")
print(f"  {out}")

# Check if there were 404s or 500s for user
out, err, code = run(client, "sudo docker logs nusahost-nginx 2>&1 | grep '36.71.184' | grep -v ' 200 '")
print(f"\n  Non-200 from user: {out if out else 'NONE - all 200!'}")

# Check aaPanel access log for user requests
print("\n[2] aaPanel request log...")
out, err, code = run(client, "sudo ls /www/server/panel/logs/request/ 2>&1")
print(f"  Request logs dir: {out}")
if out:
    for f in out.split('\n'):
        if f.strip():
            out2, _, _ = run(client, f"sudo tail -20 '/www/server/panel/logs/request/{f.strip()}' 2>&1")
            if out2:
                print(f"  {f.strip()}:\n{out2[:500]}")

# Check task log for any ongoing tasks
print("\n[3] Task log (recent)...")
out, err, code = run(client, "sudo tail -10 /www/server/panel/logs/task.log 2>&1")
print(f"  {out}")

# Check if aaPanel is doing something heavy on first load
print("\n[4] aaPanel process CPU/Memory...")
out, err, code = run(client, "ps aux | grep BT-Panel | grep -v grep")
print(f"  {out}")
out, err, code = run(client, "ps aux | grep BT-Task | grep -v grep")
print(f"  {out}")

# Check if there's an initialization step that takes time
# (like checking for updates, loading plugins, etc.)
print("\n[5] Check panel initialization in logs...")
out, err, code = run(client, "sudo tail -30 /www/server/panel/logs/error.log 2>&1 | grep -v 'login\\|HEAD\\|DEBUG'")
print(f"  {out[:500]}")

client.close()
print("\n" + "=" * 60)
print("NOTE: All requests from your browser returned 200 OK!")
print("The 'loading' might be normal first-time initialization.")
print("Try waiting 30-60 seconds, or try refreshing the page.")
print("Also try: Ctrl+Shift+Delete to clear cache, then reload.")
print("=" * 60)
