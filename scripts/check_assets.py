#!/usr/bin/env python3
"""Find correct login JS file and check login page structure"""
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

# 1. List all JS files
print("[1] All JS files in vite...")
out, err, code = run(client, "sudo ls -la /www/server/panel/BTPanel/static/vite/js/ 2>&1")
print(out[:1500])

# 2. Get the login page HTML and check what JS/CSS it loads
print("\n[2] Login page HTML (script/link tags)...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' --connect-timeout 5 2>&1 | grep -iE '<script|<link|<style' | head -20")
print(f"  {out}")

# 3. Check the login template
print("\n[3] Login template file...")
out, err, code = run(client, "sudo ls -la /www/server/panel/BTPanel/templates/default/login.html 2>&1")
print(f"  {out}")

out, err, code = run(client, "sudo head -80 /www/server/panel/BTPanel/templates/default/login.html 2>&1")
print(out[:2000])

# 4. Check what CSS files exist
print("\n[4] CSS files...")
out, err, code = run(client, "sudo ls /www/server/panel/BTPanel/static/vite/css/ 2>&1")
print(f"  {out}")

client.close()
