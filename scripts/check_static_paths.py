#!/usr/bin/env python3
"""Fix: Login button not showing - static assets path issue"""
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

# Check what static paths the login page references
print("[1] Check static asset paths in login page...")
out, err, code = run(client, """curl -s 'http://localhost/panel/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -oE '/static/[^ "'\''<>]+' | sort -u | head -20""")
print(f"  Static refs: {out}")

# Check if static files are accessible through /panel/static/
print("\n[2] Test static file access...")
tests = [
    "curl -sI 'http://localhost/static/vite/favicon.ico' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1",
    "curl -sI 'http://localhost/panel/static/vite/favicon.ico' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1",
    "curl -sI 'http://localhost/static/js/md5.js' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1",
    "curl -sI 'http://localhost/panel/static/js/md5.js' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1",
]
for t in tests:
    out, err, code = run(client, t)
    short = t.split("curl -sI '")[1].split("'")[0]
    print(f"  {short}: {out}")

client.close()
