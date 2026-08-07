#!/usr/bin/env python3
"""Diagnose and fix: aaPanel login function crash"""
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

print("=" * 60)
print("FIX: aaPanel Login Function Crash")
print("=" * 60)

# 1. Find and examine the login route
print("\n[1] Find login route definition...")
out, err, code = run(client, "sudo grep -rn 'def login' /www/server/panel/BTPanel/ 2>/dev/null | grep -v '.pyc' | grep -v '__pycache__'")
print(f"  Login function: {out[:500]}")

# 2. Check the login view code
print("\n[2] Read login view code...")
out, err, code = run(client, "sudo grep -rn 'def login' /www/server/panel/BTPanel/routes/ 2>/dev/null | grep -v '.pyc'")
print(f"  Login in routes: {out}")

# Find the exact file
if out:
    files = set()
    for line in out.split('\n'):
        if ':' in line:
            files.add(line.split(':')[0])
    for f in files:
        print(f"\n  --- File: {f} ---")
        out2, _, _ = run(client, f"sudo cat {f}")
        print(f"  {out2[:2000]}")

# 3. Check if there's a panel_ssl_switch issue
print("\n[3] Check SSL switch session issue...")
out, err, code = run(client, "sudo ls -la /www/server/panel/data/panel_ssl_switch.json 2>&1")
print(f"  SSL switch file: {out if out else 'NOT FOUND'}")

# 4. Try enabling debug mode to get better error messages
print("\n[4] Enable debug mode...")
out, err, code = run(client, "sudo touch /www/server/panel/data/debug.pl 2>&1")
print(f"  Debug enabled: code={code}")

# 5. Restart with debug
print("\n[5] Restart aaPanel with debug...")
out, err, code = run(client, "sudo bt restart 2>&1")
print(f"  Restart: {out if out else 'done'}")
time.sleep(3)

# 6. Test and check error
print("\n[6] Test login with debug mode...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' --connect-timeout 5 2>&1")
print(f"  Response: {out[:500]}")

# 7. Check error log with more detail
print("\n[7] Full error log...")
out, err, code = run(client, "sudo cat /www/server/panel/logs/error.log 2>&1")
print(f"  Error log:\n{out[:2000]}")

# 8. Check panel version
print("\n[8] Panel version...")
out, err, code = run(client, "sudo cat /www/server/panel/data/version.pl 2>&1")
print(f"  Version: {out}")

out, err, code = run(client, "sudo cat /www/server/panel/data/pyversion.pl 2>&1")
print(f"  Python version: {out}")

# 9: Try updating aaPanel to fix potential bugs
print("\n[9] Try updating aaPanel...")
# First check current version and update script
out, err, code = run(client, "sudo /www/server/panel/pyenv/bin/pip3 list 2>&1 | grep -i panel")
print(f"  Panel packages: {out}")

# Check if there's a built-in update mechanism
out, err, code = run(client, "which bt 2>&1 && sudo bt 2>&1 | head -20")
print(f"  bt command: {out[:500]}")

# 10: Check if session/secret key exists
print("\n[10] Check panel secret key and session data...")
out, err, code = run(client, "sudo cat /www/server/panel/data/pl.pl 2>&1 | head -5")
print(f"  Secret key (first 5 chars): {out[:100]}")

# 11: Maybe the issue is related to session cookie with HTTPS
# When SSL is on, Flask sets secure cookies which may cause issues
# Let's check the session configuration
print("\n[11] Check Flask session config in app.py...")
out, err, code = run(client, "sudo grep -A10 'SESSION' /www/server/panel/BTPanel/app.py 2>/dev/null")
print(f"  Session config:\n{out[:500]}")

client.close()
print("\n" + "=" * 60)
