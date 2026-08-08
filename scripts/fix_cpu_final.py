#!/usr/bin/env python3
"""Fix: Disable BT-Task, enable debug, stabilize CPU"""
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

# 1. Enable debug mode
print("[1] Enable debug mode...")
run(client, "sudo touch /www/server/panel/data/debug.pl")

# 2. Kill BT-Task
print("[2] Kill BT-Task...")
run(client, "sudo killall -9 BT-Task 2>/dev/null")
time.sleep(1)

# 3. Disable BT-Task from starting
print("[3] Disable BT-Task script...")
run(client, "sudo chmod -x /www/server/panel/BT-Task 2>/dev/null")
run(client, "sudo chmod -x /www/server/panel/pyenv/bin/python3 /www/server/panel/BT-Task 2>/dev/null")

# 4. Restart aaPanel (BT-Panel only)
print("[4] Restart aaPanel...")
run(client, "sudo bt restart 2>&1")
time.sleep(8)

# 5. Kill BT-Task again (it might have auto-started)
run(client, "sudo killall -9 BT-Task 2>/dev/null")
time.sleep(2)

# 6. Check CPU
print("[5] Check CPU...")
out, _, _ = run(client, "top -bn1 | grep '%Cpu'")
print(f"  {out}")

# 7. Check processes
out, _, _ = run(client, "ps aux | grep -E 'BT-Panel|BT-Task' | grep -v grep")
print(f"  Processes: {out}")

# 8. Test
print("[6] Test...")
tests = [
    "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s' -o /dev/null 2>&1",
    "curl -sk 'https://127.0.0.1:36977/code' --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s' -o /dev/null 2>&1",
    "curl -sk 'https://127.0.0.1:36977/userLang?action=get_language' -X POST --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s' -o /dev/null 2>&1",
]
for t in tests:
    out, _, _ = run(client, t)
    print(f"  {out}")

# 9. Check CPU again
out, _, _ = run(client, "top -bn1 | grep '%Cpu'")
print(f"\n  Final CPU: {out}")

client.close()
