#!/usr/bin/env python3
"""Check theme_config import and fix the login issue"""
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

# 1. Check theme_config module
print("[1] Check theme_config...")
out, err, code = run(client, "sudo ls -la /www/server/panel/class_v2/theme_config.py 2>&1")
print(f"  {out}")

out, err, code = run(client, "sudo ls -la /www/server/panel/class_v2/ 2>&1")
print(f"  class_v2 dir: {out}")

# 2. The real issue might be that error only shows for HEAD request
# The error log shows: "Exception on /613ccb60/ [HEAD]"
# But NOT for GET. Let's test with GET specifically
print("\n[2] Test with explicit GET...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -X GET -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | head -30")
print(f"  GET response: {out[:600]}")

# 3. The error only says HEAD, maybe GET works fine?
# Let's check the error log more carefully
print("\n[3] Full error log...")
out, err, code = run(client, "sudo cat /www/server/panel/logs/error.log 2>&1")
print(f"  {out[:2000]}")

# 4. The error is on HEAD method - that's the initial request browsers send
# When browser navigates, it first sends HEAD then GET
# The HEAD is failing because the login view doesn't handle HEAD method
# This is actually a bug in aaPanel, but maybe we can work around it

# 5. Actually wait - the curl test with HEAD shows 500
# but the actual error in the log is the view returning None for HEAD
# Let me check the method handling

# 6. Most importantly - let me test with a browser-like GET
print("\n[4] Browser-like GET with full headers...")
out, err, code = run(client, """curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' -H 'Accept: text/html,application/xhtml+xml' --connect-timeout 5 -D /tmp/headers.txt 2>&1 | head -50""")
print(f"  Response: {out[:800]}")

out, err, code = run(client, "sudo cat /tmp/headers.txt 2>&1")
print(f"  Headers: {out}")

# 7. Maybe the issue is simpler - the error log only shows HEAD errors
# Let me check if a fresh GET (not after HEAD) works
print("\n[5] Check error log for GET vs HEAD errors...")
out, err, code = run(client, "sudo grep -c 'HEAD' /www/server/panel/logs/error.log 2>&1")
print(f"  HEAD errors: {out}")

out, err, code = run(client, "sudo grep -c 'GET' /www/server/panel/logs/error.log 2>&1")
print(f"  GET errors: {out}")

client.close()
