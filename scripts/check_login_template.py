#!/usr/bin/env python3
"""Check aaPanel login template and fix"""
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

# 1. Read the FULL login function to see what it returns for GET
print("[1] Full login function (v1.py)...")
out, err, code = run(client, "sudo sed -n '1159,1260p' /www/server/panel/BTPanel/routes/v1.py 2>/dev/null")
print(out)

# 2. Check the __init__.py login function 
print("\n[2] Login function in __init__.py...")
out, err, code = run(client, "sudo sed -n '2610,2720p' /www/server/panel/BTPanel/__init__.py 2>/dev/null")
print(out)

# 3. Check if login template exists
print("\n[3] Login template files...")
out, err, code = run(client, "sudo find /www/server/panel/BTPanel/templates -name '*login*' 2>/dev/null")
print(f"  {out}")

out, err, code = run(client, "sudo ls /www/server/panel/BTPanel/templates/ 2>/dev/null")
print(f"  Templates dir: {out[:300]}")

# 4. Check v2 login function  
print("\n[4] Login v2 function...")
out, err, code = run(client, "sudo sed -n '1203,1310p' /www/server/panel/BTPanel/routes/v2.py 2>/dev/null")
print(out)

# 5. Check the v2 login_wp function
print("\n[5] Login wp function...")
out, err, code = run(client, "sudo sed -n '2352,2400p' /www/server/panel/BTPanel/routes/v2.py 2>/dev/null")
print(out)

# 6. Check what route is actually being used for /613ccb60/
print("\n[6] URL routing rules...")
out, err, code = run(client, "sudo grep -n '613ccb60\\|admin_path\\|route_path' /www/server/panel/BTPanel/__init__.py 2>/dev/null | head -20")
print(f"  {out}")

# 7. Check admin_path
out, err, code = run(client, "sudo cat /www/server/panel/data/admin_path.pl 2>/dev/null")
print(f"\n[7] Admin path: {out}")

# 8. Check for install.pl (fresh install marker)
out, err, code = run(client, "sudo ls -la /www/server/panel/data/install.pl 2>/dev/null")
print(f"\n[8] Install marker: {out if out else 'NOT FOUND'}")

# 9. Check if panel was initialized properly
print("\n[9] Panel data files...")
out, err, code = run(client, "sudo ls -la /www/server/panel/data/ 2>/dev/null")
print(f"  {out[:600]}")

client.close()
