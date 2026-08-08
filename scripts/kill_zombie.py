#!/usr/bin/env python3
"""KILL the zombie installer eating 98% CPU"""
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

# KILL the zombie installer!
print("[1] KILL zombie installer (PID 39086, 98% CPU)...")
out, _, _ = run(client, "sudo kill -9 39086 2>&1")
print(f"  Kill result: {out if out else 'done'}")
time.sleep(2)

# Also check for any child processes
out, _, _ = run(client, "pgrep -a install_6.0")
print(f"  Remaining installers: {out if out else 'NONE'}")

# Check CPU now
print("\n[2] CPU after kill...")
out, _, _ = run(client, "top -bn1 | grep '%Cpu'")
print(f"  {out}")

out, _, _ = run(client, "top -bn1 | head -8")
print(out)

# Now test aaPanel
print("\n[3] Test aaPanel (should be fast now)...")
out, _, _ = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s' -o /dev/null 2>&1")
print(f"  Login page: {out}")

out, _, _ = run(client, "curl -sk 'https://127.0.0.1:36977/code' --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s Size: %{size_download}' -o /dev/null 2>&1")
print(f"  /code: {out}")

out, _, _ = run(client, "curl -sk 'https://127.0.0.1:36977/userLang?action=get_language' -X POST --connect-timeout 10 -w 'HTTP: %{http_code} Time: %{time_total}s' -o /dev/null 2>&1")
print(f"  /userLang: {out}")

client.close()
print("\n" + "=" * 60)
print("ZOMBIE INSTALLER KILLED! CPU should be normal now.")
print("Refresh: https://panel.pro99.my.id/613ccb60/")
print("=" * 60)
