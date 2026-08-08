#!/usr/bin/env python3
"""Fix aaPanel: Properly disable SSL via aaPanel CLI, or use HTTPS approach"""
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
print("FIX: aaPanel SSL - Proper approach")
print("=" * 60)

# The real issue: aaPanel's builtin webserver (nginx binary) handles SSL
# When SSL cert files are missing, the webserver conf is broken -> 404
# When SSL is on, browser needs to accept self-signed cert -> connection reset if not
# 
# BEST APPROACH: Restore everything, use HTTPS with self-signed cert
# The browser "connection reset" was because Docker nginx was intercepting port 36977
# Now that we removed the Docker nginx 36977 proxy, aaPanel's webserver handles it directly
# We just need the cert files back and the webserver to start properly

# Step 1: Restore cert files
print("\n[1] Ensure SSL cert files exist...")
out, err, code = run(client, "sudo ls -la /www/server/panel/ssl/ 2>&1")
print(f"  SSL dir: {out}")

# If backup exists but cert doesn't, restore
out, err, code = run(client, "test -f /www/server/panel/ssl/certificate.pem && echo 'EXISTS' || echo 'MISSING'")
if out.strip() == 'MISSING':
    print("  Restoring certificate.pem from backup...")
    run(client, "sudo cp /www/server/panel/ssl/certificate.pem.bak /www/server/panel/ssl/certificate.pem 2>&1")
    
out, err, code = run(client, "test -f /www/server/panel/ssl/privateKey.pem && echo 'EXISTS' || echo 'MISSING'")
if out.strip() == 'MISSING':
    print("  Restoring privateKey.pem from backup...")
    run(client, "sudo cp /www/server/panel/ssl/privateKey.pem.bak /www/server/panel/ssl/privateKey.pem 2>&1")

# Step 2: Check generated webserver config
print("\n[2] Check generated webserver config...")
out, err, code = run(client, "sudo cat /www/server/panel/webserver/conf/webserver.conf 2>&1")
print(f"  webserver.conf:\n{out}")

# Step 3: Check template files
print("\n[3] Check webserver template (HTTP)...")
out, err, code = run(client, "sudo cat /www/server/panel/webserver/tpls/webserver.conf 2>&1")
print(f"  Template:\n{out}")

print("\n[4] Check webserver listen template...")
out, err, code = run(client, "sudo cat /www/server/panel/webserver/tpls/webserver_listen.conf 2>&1")
print(f"  Listen template:\n{out}")

# Step 5: Look at how webserver.py generates the config
print("\n[5] Check webserver.py config generation logic...")
out, err, code = run(client, "sudo grep -n 'webserver.conf\\|ssl\\|template\\|generate' /www/server/panel/class/webserver.py 2>/dev/null | head -30")
print(f"  Config generation:\n{out}")

# Step 6: Stop everything and regenerate config
print("\n[6] Stop aaPanel, regenerate webserver config...")
out, err, code = run(client, "sudo bt stop 2>&1")
print(f"  Stop: {out if out else 'done'}")

time.sleep(2)

# Remove the generated conf so it gets regenerated
out, err, code = run(client, "sudo rm -f /www/server/panel/webserver/conf/webserver.conf 2>&1")
print(f"  Remove old conf: code={code}")

# Start aaPanel (it will regenerate the webserver config)
print("\n[7] Start aaPanel (regenerates config)...")
out, err, code = run(client, "sudo bt start 2>&1")
print(f"  Start: {out if out else 'done'}")

time.sleep(5)

# Step 8: Check if new config was generated
print("\n[8] Check regenerated webserver config...")
out, err, code = run(client, "sudo cat /www/server/panel/webserver/conf/webserver.conf 2>&1")
print(f"  New config:\n{out}")

# Step 9: Test access
print("\n[9] Test access...")
out, err, code = run(client, "curl -sk https://127.0.0.1:36977/ --connect-timeout 5 2>&1 | head -20")
print(f"  HTTPS root: {out[:400]}")

out, err, code = run(client, "curl -sk https://127.0.0.1:36977/613ccb60/ --connect-timeout 5 2>&1 | head -20")
print(f"  HTTPS security path: {out[:400]}")

out, err, code = run(client, "curl -skI https://127.0.0.1:36977/ --connect-timeout 5 2>&1")
print(f"  HTTPS headers: {out[:400]}")

# HTTP test
out, err, code = run(client, "curl -sI http://127.0.0.1:36977/ --connect-timeout 5 2>&1")
print(f"  HTTP headers: {out[:400]}")

client.close()
print("\n" + "=" * 60)
