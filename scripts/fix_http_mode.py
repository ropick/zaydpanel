#!/usr/bin/env python3
"""Diagnose loading issue - try HTTP mode and check for JS errors"""
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

# The issue might be that the browser shows the SSL warning page and the user
# thinks the page is "loading". Let me try to make aaPanel work on HTTP too.
# 
# Better approach: set up aaPanel behind Docker nginx with SSL termination
# so the user can access via https://staging.pro99.my.id:36977/ with proper Cloudflare SSL

# But for now, let me check what the actual page returns to external access

# 1. Check if page loads from external (using IP)
print("[1] External access test...")
out, err, code = run(client, "curl -sk 'https://168.110.210.148:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' --connect-timeout 10 -w '\\nHTTP_CODE: %{http_code}\\nSIZE: %{size_download}\\nTIME: %{time_total}' 2>&1 | tail -5")
print(f"  {out}")

# 2. Check if there's a loading spinner in the page that might get stuck
print("\n[2] Check for loading/overlay elements...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -oiE 'loading|spinner|overlay|mask|skeleton|progress|wait' | sort | uniq -c | sort -rn | head -10")
print(f"  Loading elements: {out}")

# 3. Check if the page has any API calls during init
print("\n[3] API calls in login page...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -oE '/[a-zA-Z_]+\\?[a-zA-Z_]*=[a-zA-Z0-9_]*|ajax|fetch|axios|XMLHttpRequest|\\$.get|\\$.post|request\\(' | head -15")
print(f"  API calls: {out}")

# 4. Check the login page bottom for initialization code
print("\n[4] Login page init section (grep for init/load/start)...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -iE 'init|onload|DOMContentLoaded|ready|setTimeout|setInterval' | head -15")
print(f"  Init code: {out}")

# 5. Check panel version and if update check causes hang
print("\n[5] Panel version info...")
out, err, code = run(client, "sudo cat /www/server/panel/data/version.pl 2>/dev/null")
print(f"  Version: {out if out else 'NOT FOUND'}")

out, err, code = run(client, "sudo cat /www/server/panel/data/update_speed.pl 2>/dev/null")
print(f"  Update speed: {out if out else 'NOT FOUND'}")

# 6. Actually the real fix: let me check if the user might just be stuck on 
# the SSL warning page. The best fix is to proxy aaPanel through Cloudflare
# so it gets a real SSL cert. Or we can use the Docker nginx as a proxy.
# 
# For now, let me try the simplest approach:
# Disable SSL in aaPanel (but keep cert files so webserver starts)
# Then user can access via HTTP without SSL warning

print("\n[6] Try HTTP-only mode for aaPanel...")
# Remove ssl.pl to disable SSL
out, err, code = run(client, "sudo rm -f /www/server/panel/data/ssl.pl 2>&1")
print(f"  ssl.pl removed: code={code}")

# Remove generated config to force regeneration
out, err, code = run(client, "sudo rm -f /www/server/panel/webserver/conf/webserver.conf 2>&1")

# Restart
out, err, code = run(client, "sudo bt restart 2>&1")
print(f"  Restart: {out if out else 'done'}")
time.sleep(5)

# Test HTTP
print("\n[7] Test HTTP access...")
out, err, code = run(client, "curl -sI 'http://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1")
print(f"  HTTP headers: {out[:400]}")

out, err, code = run(client, "curl -s 'http://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | head -5")
print(f"  HTTP body start: {out[:300]}")

client.close()
