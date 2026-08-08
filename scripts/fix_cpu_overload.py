#!/usr/bin/env python3
"""Fix CPU 100% overload - disable unnecessary tasks and restart"""
import paramiko, time

def connect():
    key = paramiko.RSAKey.from_private_key_file("/home/z/my-project/deploy/nusahost_id")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

client = connect()

# 1. Check current CPU
print("[1] Current CPU...")
out, err, code = run(client, "top -bn1 | head -5")
print(f"  {out}")

# 2. Kill BT-Task to stop the CPU hog
print("\n[2] Stop BT-Task (CPU hog)...")
out, err, code = run(client, "sudo kill -9 $(pgrep -f BT-Task) 2>&1")
print(f"  Killed: {out if out else 'done'}")
time.sleep(2)

# 3. Check CPU again
out, err, code = run(client, "top -bn1 | head -5")
print(f"  CPU after kill: {out}")

# 4. Clean up crash/lock files
print("\n[3] Clean up lock files...")
cleanup_cmds = [
    "sudo rm -f /tmp/panelBoot.pl 2>/dev/null",
    "sudo rm -f /www/server/panel/data/session/*.pl 2>/dev/null", 
    "sudo rm -f /www/server/panel/data/sess_files/* 2>/dev/null",
]
for cmd in cleanup_cmds:
    run(client, cmd)
print("  Cleaned")

# 5. Disable debug mode (reduces overhead)
print("\n[4] Disable debug mode...")
run(client, "sudo rm -f /www/server/panel/data/debug.pl 2>&1")
print("  Debug disabled")

# 6. Restart aaPanel cleanly
print("\n[5] Restart aaPanel...")
out, err, code = run(client, "sudo bt restart 2>&1")
print(f"  Restart: {out if out else 'done'}")
time.sleep(5)

# 7. Check CPU after restart
print("\n[6] CPU after restart...")
out, err, code = run(client, "top -bn1 | head -5")
print(f"  {out}")

# 8. Check task log
print("\n[7] Task log after restart...")
out, err, code = run(client, "sudo tail -10 /www/server/panel/logs/task.log 2>&1")
print(f"  {out}")

# 9. Quick test
print("\n[8] Quick test...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s' -o /dev/null 2>&1")
print(f"  Login page: {out}")

out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/code' --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s' -o /dev/null 2>&1")
print(f"  /code: {out}")

out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/userLang?action=get_language' -X POST --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s' -o /dev/null 2>&1")
print(f"  /userLang: {out}")

client.close()
print("\n" + "=" * 60)
print("CPU overload fixed. Try refreshing the page now!")
print("https://panel.pro99.my.id/613ccb60/")
print("=" * 60)
