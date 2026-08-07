#!/usr/bin/env python3
"""Restore SSL mode and verify it works"""
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

# Restore SSL
print("[1] Restore SSL...")
run(client, "echo '1' | sudo tee /www/server/panel/data/ssl.pl")
run(client, "sudo rm -f /www/server/panel/webserver/conf/webserver.conf")

out, err, code = run(client, "sudo bt restart 2>&1")
print(f"  Restart: {out if out else 'done'}")
time.sleep(5)

# Verify HTTPS works
print("\n[2] Verify HTTPS...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' --connect-timeout 5 -o /dev/null -w 'HTTP_CODE: %{http_code} SIZE: %{size_download}' 2>&1")
print(f"  {out}")

# Test HTTP (to confirm it redirects or fails)
out, err, code = run(client, "curl -sI 'http://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1")
print(f"\n  HTTP (non-SSL) response: {out[:200]}")

# Check that HTTP redirects to HTTPS
out, err, code = run(client, "curl -sI 'http://127.0.0.1:36977/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 -L --max-redirs 0 2>&1")
print(f"\n  HTTP root response: {out[:300]}")

client.close()
