#!/usr/bin/env python3
"""Deep fix: Remove aaPanel SSL certificate and disable HTTPS redirect completely"""
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
print("DEEP FIX: Remove aaPanel SSL + HTTPS Redirect")
print("=" * 60)

# Step 1: Check aaPanel webserver config for SSL
print("\n[1] Check aaPanel webserver config...")
out, err, code = run(client, "sudo cat /www/server/panel/webserver/conf/webserver.con 2>&1")
print(f"  webserver.con:\n{out}")

# Step 2: Check SSL template config
print("\n[2] Check SSL template config...")
out, err, code = run(client, "sudo cat /www/server/panel/webserver/tpls/webserver_ssl.conf 2>&1")
print(f"  SSL template:\n{out}")

# Step 3: Check all SSL-related data files
print("\n[3] SSL data files...")
cmds = [
    "sudo ls -la /www/server/panel/data/ssl* 2>&1",
    "sudo ls -la /www/server/panel/data/*.pl 2>&1",
    "sudo cat /www/server/panel/data/ssl_certificate_file.pl 2>&1",
    "sudo cat /www/server/panel/data/ssl_private_key_file.pl 2>&1",
]
for cmd in cmds:
    out, err, code = run(client, cmd)
    print(f"  {cmd.split('/')[-1]}: {out[:200] if out else 'N/A'}")

# Step 4: Remove SSL certificate files to force disable
print("\n[4] Remove SSL certificate files...")
out, err, code = run(client, "sudo mv /www/server/panel/ssl/certificate.pem /www/server/panel/ssl/certificate.pem.bak 2>&1")
print(f"  Backup cert: {out if out else 'done'}")
out, err, code = run(client, "sudo mv /www/server/panel/ssl/privateKey.pem /www/server/panel/ssl/privateKey.pem.bak 2>&1")
print(f"  Backup key: {out if out else 'done'}")

# Step 5: Set SSL to false in all possible locations
print("\n[5] Force disable SSL in all config files...")
out, err, code = run(client, "echo '0' | sudo tee /www/server/panel/data/ssl.pl")
print(f"  ssl.pl = 0: {out.strip()}")

# Check for SSL index file
out, err, code = run(client, "sudo cat /www/server/panel/data/ssl_index.pl 2>&1")
print(f"  ssl_index.pl: {out if out else 'N/A'}")

# Step 6: Restart aaPanel
print("\n[6] Restart aaPanel...")
out, err, code = run(client, "sudo bt restart 2>&1")
print(f"  Restart: {out if out else 'done'}")

time.sleep(3)

# Step 7: Test again
print("\n[7] Test aaPanel access...")
out, err, code = run(client, "curl -sI http://127.0.0.1:36977/ --connect-timeout 5 2>&1")
print(f"  curl 127.0.0.1:36977: {out[:400] if out else 'FAILED'}")

if "302" in out and "https" in out.lower():
    print("  STILL redirecting. Checking more...")
    
    # Check what the webserver binary is and its args
    out, err, code = run(client, "ps aux | grep webserver | grep -v grep")
    print(f"  webserver process: {out}")
    
    # Check aaPanel's Python code for redirect logic
    out, err, code = run(client, "sudo grep -rn 'redirect\\|302\\|301' /www/server/panel/webserver/ 2>/dev/null | grep -v '.pyc' | head -20")
    print(f"  Redirect in webserver dir: {out[:600]}")
    
    # Check if there's a site config with SSL
    out, err, code = run(client, "sudo find /www/server/panel/vhost/ -name '*.conf' 2>/dev/null")
    print(f"  vhost configs: {out}")
    
    for f in out.split('\n'):
        if f.strip():
            content, _, _ = run(client, f"sudo cat {f.strip()} 2>&1")
            if content:
                print(f"  --- {f.strip()} ---")
                print(content[:500])

# Step 8: Check aaPanel API for SSL setting
print("\n[8] Check aaPanel API/config for SSL settings...")
out, err, code = run(client, "sudo cat /www/server/panel/BTPanel/__init__.py 2>/dev/null | grep -i 'ssl\\|https\\|redirect' | head -20")
print(f"  BTPanel __init__: {out[:500]}")

out, err, code = run(client, "sudo grep -rn 'ssl_redirect\\|to_https\\|force_ssl' /www/server/panel/BTPanel/ 2>/dev/null | grep -v '.pyc' | head -10")
print(f"  SSL redirect code: {out[:500]}")

client.close()
print("\n" + "=" * 60)
