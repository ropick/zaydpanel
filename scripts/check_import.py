#!/usr/bin/env python3
"""Fix: Check Python path and common module import"""
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

# 1. Check if BT-Panel adds class/ to sys.path
print("[1] Check BT-Panel startup and sys.path...")
out, err, code = run(client, "sudo head -50 /www/server/panel/BT-Panel 2>&1")
print(f"  BT-Panel head:\n{out}")

# 2. Check common.py content for panelSetup
print("\n[2] Check panelSetup class in common.py...")
out, err, code = run(client, "sudo grep -n 'class panelSetup' /www/server/panel/class/common.py 2>&1")
print(f"  panelSetup: {out}")

if not out:
    print("  panelSetup NOT FOUND in common.py!")
    print("  Searching all .py files...")
    out, err, code = run(client, "sudo grep -rn 'class panelSetup' /www/server/panel/class/ 2>/dev/null | grep -v '.pyc' | grep -v __pycache__")
    print(f"  {out}")
    
    # Check the installed version - maybe it's a different structure
    out, err, code = run(client, "sudo head -50 /www/server/panel/class/common.py 2>&1")
    print(f"\n  common.py head:\n{out}")

# 3. Check if maybe the installed version is newer and common.py structure changed
print("\n[3] Check common.py line count and classes...")
out, err, code = run(client, "sudo wc -l /www/server/panel/class/common.py 2>&1")
print(f"  Lines: {out}")
out, err, code = run(client, "sudo grep -n 'class ' /www/server/panel/class/common.py 2>&1")
print(f"  Classes: {out}")

# 4. Let me check what the panelSetup.init() actually does
# Maybe the init function just checks some setup requirements
# and returns a redirect or error page
print("\n[4] Search for panelSetup across all panel files...")
out, err, code = run(client, "sudo grep -rn 'panelSetup' /www/server/panel/class/ /www/server/panel/BTPanel/ 2>/dev/null | grep -v '.pyc' | grep -v __pycache__ | head -20")
print(f"  {out}")

# 5. Check the __init__.py for the import
print("\n[5] Import statement context in __init__.py...")
out, err, code = run(client, "sudo sed -n '440,450p' /www/server/panel/BTPanel/__init__.py 2>&1")
print(f"  Import context:\n{out}")

# 6. Check panelSetup().init() return value more carefully
# Maybe it's returning None when it should return None (no error)
# and the code just falls through
print("\n[6] Read the critical section in __init__.py around init()...")
out, err, code = run(client, "sudo sed -n '2740,2770p' /www/server/panel/BTPanel/__init__.py 2>&1")
print(f"  Critical section:\n{out}")

# Also check v1.py equivalent
out, err, code = run(client, "sudo sed -n '1260,1295p' /www/server/panel/BTPanel/routes/v1.py 2>&1")
print(f"\n  v1.py critical section:\n{out}")

# 7. Try running BT-Panel with PYTHONPATH set and capture output
print("\n[7] Test import directly...")
out, err, code = run(client, "sudo PYTHONPATH=/www/server/panel/class /www/server/panel/pyenv/bin/python3 -c 'import common; print(common.__file__); print(dir(common))' 2>&1")
print(f"  Import test: {out[:500]}")

client.close()
