#!/usr/bin/env python3
"""Find and fix aaPanel login function crash"""
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

# 1. Find login route
print("[1] Login route files...")
out, err, code = run(client, "sudo grep -rn 'def login' /www/server/panel/BTPanel/ 2>/dev/null | grep -v '.pyc' | grep -v __pycache__")
print(f"  {out}")

# 2. Read the login route file
print("\n[2] Login route code...")
# Find the route file
out2, err, code = run(client, "sudo grep -rl 'def login' /www/server/panel/BTPanel/routes/ 2>/dev/null | grep -v '.pyc'")
print(f"  Route file: {out2}")

if out2.strip():
    # Get just the login function
    out3, err, code = run(client, f"sudo grep -A60 'def login' {out2.strip().split(chr(10))[0]} 2>/dev/null")
    print(f"  Login function:\n{out3[:2000]}")

# 3. Check panel version
print("\n[3] Panel version...")
out, err, code = run(client, "sudo cat /www/server/panel/data/version.pl 2>/dev/null")
print(f"  {out}")

# 4. Check Flask session SSL config
print("\n[4] Session SSL config...")
out, err, code = run(client, "sudo grep -B2 -A10 'SESSION_COOKIE_SECURE\\|SESSION_COOKIE' /www/server/panel/BTPanel/app.py 2>/dev/null")
print(f"  {out[:600]}")

# 5. Check panel_ssl_switch
out, err, code = run(client, "sudo cat /www/server/panel/data/panel_ssl_switch.json 2>/dev/null")
print(f"\n[5] SSL switch: {out if out else 'NOT FOUND'}")

# 6. Try the simplest fix: just run the update script
print("\n[6] Panel update check...")
out, err, code = run(client, "sudo cat /www/server/panel/class/panelPlugin.py 2>/dev/null | grep -n 'update' | head -5")
print(f"  {out}")

# 7. Check if this is a known issue - read the install log for errors
print("\n[7] Install log (last 50 lines)...")
out, err, code = run(client, "sudo tail -50 /www/server/panel/logs/error.log 2>/dev/null")
print(f"  {out[:1500]}")

client.close()
