#!/usr/bin/env python3
"""Find panelSetup class anywhere in BTPanel"""
import paramiko

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

# 1. Find panelSetup class everywhere
print("[1] Find panelSetup class...")
out, err, code = run(client, "sudo grep -rn 'class panelSetup' /www/server/panel/BTPanel/ 2>/dev/null | grep -v '.pyc' | grep -v __pycache__")
print(f"  {out}")

# 2. Maybe it's defined differently
print("\n[2] Find panelSetup definition...")
out, err, code = run(client, "sudo grep -rn 'panelSetup' /www/server/panel/BTPanel/__init__.py 2>/dev/null | head -10")
print(f"  {out}")

# 3. Check the import in __init__.py
print("\n[3] Imports in __init__.py...")
out, err, code = run(client, "sudo head -30 /www/server/panel/BTPanel/__init__.py 2>/dev/null")
print(f"  {out}")

# 4. Check common module import
print("\n[4] common module...")
out, err, code = run(client, "sudo grep -n 'import common\\|from common' /www/server/panel/BTPanel/__init__.py 2>/dev/null | head -5")
print(f"  {out}")

# 5. List common.py file info
print("\n[5] common.py info...")
out, err, code = run(client, "sudo wc -l /www/server/panel/BTPanel/common.py 2>/dev/null")
print(f"  Lines: {out}")

out, err, code = run(client, "sudo grep -n 'class ' /www/server/panel/BTPanel/common.py 2>/dev/null | head -20")
print(f"  Classes: {out}")

# 6. The init might be returning a maintenance page or similar
# Let's check if there's a close.pl or maintenance mode
print("\n[6] Check maintenance/close mode...")
out, err, code = run(client, "sudo ls -la /www/server/panel/data/close.pl 2>/dev/null")
print(f"  close.pl: {out if out else 'NOT FOUND'}")

out, err, code = run(client, "sudo ls -la /www/server/panel/data/maintenance* 2>/dev/null")
print(f"  maintenance: {out if out else 'NOT FOUND'}")

# 7. Check aapanel-maintenance dir
out, err, code = run(client, "sudo ls -la /www/server/panel/data/aapanel-maintenance/ 2>/dev/null")
print(f"  maintenance dir: {out if out else 'NOT FOUND'}")

# 8. Let's try a more direct approach - enable debug and test
print("\n[8] Enable debug and test...")
run(client, "sudo touch /www/server/panel/data/debug.pl 2>/dev/null")
run(client, "sudo bt restart 2>/dev/null")

import time
time.sleep(3)

# Test with full verbose
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'Accept: text/html' --connect-timeout 5 2>&1")
print(f"  Response: {out[:500]}")

# 9. Get the latest error from error log
out, err, code = run(client, "sudo tail -50 /www/server/panel/logs/error.log 2>/dev/null")
print(f"\n  Latest error:\n{out[:2000]}")

client.close()
