#!/usr/bin/env python3
"""Read the rest of the login function and find the GET handler"""
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

# Read the END of login function in __init__.py (lines 2610-2800)
print("[1] Login function continuation (__init__.py lines 2610-2800)...")
out, err, code = run(client, "sudo sed -n '2610,2800p' /www/server/panel/BTPanel/__init__.py 2>/dev/null")
print(out)

# Read the END of login function in v1.py (lines 1220-1320)
print("\n[2] Login function continuation (v1.py lines 1220-1320)...")
out, err, code = run(client, "sudo sed -n '1220,1320p' /www/server/panel/BTPanel/routes/v1.py 2>/dev/null")
print(out)

# Check the is_login function
print("\n[3] is_login function...")
out, err, code = run(client, "sudo grep -n 'def is_login' /www/server/panel/BTPanel/__init__.py 2>/dev/null")
print(f"  {out}")
if out:
    line_num = out.split(':')[0].strip()
    out2, _, _ = run(client, f"sudo sed -n '{line_num},{int(line_num)+30}p' /www/server/panel/BTPanel/__init__.py 2>/dev/null")
    print(f"  {out2}")

# Check panelSetup().init() - this is called during login and might return error
print("\n[4] panelSetup init function...")
out, err, code = run(client, "sudo grep -n 'def init' /www/server/panel/BTPanel/common.py 2>/dev/null | head -5")
print(f"  {out}")
if out:
    line_num = out.split(':')[0].strip()
    out2, _, _ = run(client, f"sudo sed -n '{line_num},{int(line_num)+50}p' /www/server/panel/BTPanel/common.py 2>/dev/null")
    print(f"  {out2}")

client.close()
