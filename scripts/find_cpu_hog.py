#!/usr/bin/env python3
"""Find CPU hog and fix /code endpoint"""
import paramiko, time

def connect():
    key = paramiko.RSAKey.from_private_key_file("/home/z/my-project/deploy/nusahost_id")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=10):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

client = connect()

# 1. Find ALL CPU hogs
print("[1] Top CPU consumers...")
out, _, _ = run(client, "ps aux --sort=-%cpu | head -15")
print(out)

# 2. Check if BT-Task is actually dead
out, _, _ = run(client, "pgrep -a BT-Task")
print(f"\n  BT-Task: {out if out else 'DEAD'}")

# 3. Check /code - why 404? It's probably because the route requires session
# Let me test with full cookie flow
print("\n[2] Test /code with proper session flow...")
out, _, _ = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' -c /tmp/c.txt --connect-timeout 5 -o /dev/null -w 'Login: %{http_code}\n' 2>&1")
print(f"  {out}")
out, _, _ = run(client, "curl -sk 'https://127.0.0.1:36977/code' -b /tmp/c.txt --connect-timeout 5 -w 'HTTP: %{http_code} Size: %{size_download}\n' -o /dev/null 2>&1")
print(f"  /code: {out}")
out, _, _ = run(client, "curl -sk 'https://127.0.0.1:36977/userLang?action=get_language' -b /tmp/c.txt -X POST --connect-timeout 5 -w 'HTTP: %{http_code}\n' 2>&1")
print(f"  /userLang: {out}")

# 4. Check the aaPanel request log for /code
print("\n[3] Request log for /code...")
out, _, _ = run(client, "sudo tail -10 /www/server/panel/logs/request/2026-08-07.json 2>&1")
print(f"  {out}")

# 5. Check if the issue is nginx (aaPanel's webserver) returning 404
# vs the Python app returning 404
print("\n[4] Check webserver error log...")
out, _, _ = run(client, "sudo tail -5 /www/server/panel/webserver/logs/error.log 2>&1")
print(f"  {out[:300]}")

client.close()
