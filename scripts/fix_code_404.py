#!/usr/bin/env python3
"""Fix /code 404 - restart aaPanel properly and test"""
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

# 1. Check current state
print("[1] Check processes...")
out, _, _ = run(client, "ps aux | grep -E 'BT-Panel|BT-Task|webserver' | grep -v grep")
print(f"  {out}")

out, _, _ = run(client, "sudo ss -tlnp | grep 36977")
print(f"  Port: {out}")

# 2. Full restart
print("\n[2] Full restart aaPanel...")
# Re-enable BT-Task script first
run(client, "sudo chmod +x /www/server/panel/BT-Task 2>/dev/null")

out, _, _ = run(client, "sudo bt restart 2>&1")
print(f"  Restart: {out if out else 'done'}")
time.sleep(5)

# 3. Kill BT-Task again (it eats CPU)
run(client, "sudo killall -9 BT-Task 2>/dev/null")
run(client, "sudo chmod -x /www/server/panel/BT-Task 2>/dev/null")
time.sleep(2)

# 4. Now test with full browser-like flow
print("\n[3] Test with proper browser flow...")
out, _, _ = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' -c /tmp/cookies.txt --connect-timeout 10 -w 'Login: %{http_code} Size: %{size_download}\n' -o /dev/null 2>&1")
print(f"  {out}")

# Show cookies
out, _, _ = run(client, "cat /tmp/cookies.txt 2>&1")
print(f"  Cookies: {out[:200]}")

out, _, _ = run(client, "curl -sk 'https://127.0.0.1:36977/code' -b /tmp/cookies.txt -H 'User-Agent: Mozilla/5.0' --connect-timeout 10 -w 'HTTP: %{http_code} Size: %{size_download} Time: %{time_total}s\n' -o /dev/null 2>&1")
print(f"  /code: {out}")

out, _, _ = run(client, "curl -sk 'https://127.0.0.1:36977/userLang?action=get_language' -b /tmp/cookies.txt -H 'User-Agent: Mozilla/5.0' -X POST --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s\n' -o /dev/null 2>&1")
print(f"  /userLang: {out}")

# 5. Check aaPanel request log
print("\n[4] Request log (latest)...")
out, _, _ = run(client, "sudo tail -5 /www/server/panel/logs/request/2026-08-07.json 2>&1")
print(f"  {out}")

# 6. Check error log
print("\n[5] Error log (latest)...")
out, _, _ = run(client, "sudo tail -5 /www/server/panel/logs/error.log 2>&1")
print(f"  {out[:500]}")

client.close()
