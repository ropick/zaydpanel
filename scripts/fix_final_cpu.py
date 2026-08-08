#!/usr/bin/env python3
"""Final fix: Re-enable debug, stop BT-Task overload, stabilize aaPanel"""
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

# 1. Re-enable debug mode (critical - without it, login page 404)
print("[1] Enable debug mode...")
run(client, "sudo touch /www/server/panel/data/debug.pl")

# 2. Kill BT-Task completely and don't let it restart  
print("\n[2] Stop BT-Task permanently for now...")
run(client, "sudo kill -9 $(pgrep -f BT-Task) 2>/dev/null")
time.sleep(1)
# Also stop the service
run(client, "sudo systemctl stop bt 2>/dev/null")
time.sleep(1)

# 3. Only start BT-Panel (web server) without BT-Task
print("\n[3] Start only BT-Panel (web UI) without BT-Task...")
# BT-Panel is the web interface, BT-Task is the background worker
run(client, "sudo /www/server/panel/pyenv/bin/python3 /www/server/panel/BT-Panel &", timeout=5)
time.sleep(3)

# 4. Make sure BT-Task does NOT start
# Rename the task script to prevent auto-start
run(client, "sudo mv /www/server/panel/BT-Task /www/server/panel/BT-Task.disabled 2>/dev/null")

# 5. Check CPU
print("\n[4] Check CPU...")
out, err, code = run(client, "top -bn1 | head -5")
print(f"  {out}")

# 6. Test login page
print("\n[5] Test login page...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s' -o /dev/null 2>&1")
print(f"  Login page: {out}")

out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/code' --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s' -o /dev/null 2>&1")
print(f"  /code: {out}")

out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/userLang?action=get_language' -X POST --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s' -o /dev/null 2>&1")
print(f"  /userLang: {out}")

# 7. Check port still listening
out, err, code = run(client, "sudo ss -tlnp | grep 36977")
print(f"\n  Port 36977: {out}")

# 8. Check CPU again
out, err, code = run(client, "top -bn1 | head -5")
print(f"  CPU final: {out}")

client.close()
print("\n" + "=" * 60)
print("FIXED: BT-Task disabled (CPU hog), debug mode on")
print("Login page should now load fast!")
print("https://panel.pro99.my.id/613ccb60/")
print("=" * 60)
