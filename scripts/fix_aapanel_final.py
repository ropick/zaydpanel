#!/usr/bin/env python3
"""Final fix: Restore SSL, restart aaPanel, verify via HTTPS"""
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
print("FINAL FIX: Restore SSL + Verify aaPanel")
print("=" * 60)

# Step 1: Restore ssl.pl (enable SSL)
print("\n[1] Enable SSL...")
out, err, code = run(client, "echo '1' | sudo tee /www/server/panel/data/ssl.pl")
print(f"  ssl.pl = 1: {out.strip()}")

# Step 2: Ensure cert files exist
print("\n[2] Verify cert files...")
out, err, code = run(client, "sudo ls -la /www/server/panel/ssl/certificate.pem /www/server/panel/ssl/privateKey.pem 2>&1")
print(f"  Certs: {out}")

# Step 3: Stop and start clean
print("\n[3] Clean restart aaPanel...")
out, err, code = run(client, "sudo bt stop 2>&1")
print(f"  Stop: {out if out else 'done'}")
time.sleep(2)

# Remove generated webserver.conf to force regeneration with SSL
out, err, code = run(client, "sudo rm -f /www/server/panel/webserver/conf/webserver.conf 2>&1")
print(f"  Remove old conf: code={code}")

out, err, code = run(client, "sudo bt start 2>&1")
print(f"  Start: {out if out else 'done'}")
time.sleep(5)

# Step 4: Check regenerated config has SSL
print("\n[4] Verify new webserver config has SSL...")
out, err, code = run(client, "sudo grep -c 'ssl_certificate\\|listen.*ssl\\|443' /www/server/panel/webserver/conf/webserver.conf 2>&1")
print(f"  SSL directives count: {out}")

# Step 5: Check port status
print("\n[5] Port status...")
out, err, code = run(client, "sudo ss -tlnp | grep 36977")
print(f"  Port 36977: {out}")

# Step 6: Test HTTPS access with -k (skip cert verification)
print("\n[6] Test HTTPS access...")
tests = [
    ("curl -skI https://127.0.0.1:36977/ --connect-timeout 5 2>&1", "Root /"),
    ("curl -skI 'https://127.0.0.1:36977/613ccb60/' --connect-timeout 5 2>&1", "Security path"),
    ("curl -sk 'https://127.0.0.1:36977/613ccb60/' --connect-timeout 5 2>&1 | head -30", "Login page body"),
]
for cmd, desc in tests:
    out, err, code = run(client, cmd)
    print(f"\n  [{desc}]:")
    print(f"  {out[:500]}")

# Step 7: Check error log
print("\n[7] Panel error log after test...")
out, err, code = run(client, "sudo tail -20 /www/server/panel/logs/error.log 2>&1")
print(f"  Errors: {out[:500] if out else 'CLEAN'}")

# Step 8: Get panel info for user
print("\n[8] Panel access info...")
out, err, code = run(client, "sudo bt default 2>&1")
print(f"  {out}")

client.close()
print("\n" + "=" * 60)
print("FINAL FIX COMPLETE")
print("=" * 60)
print("\nACTION NEEDED BY USER:")
print("1. Open browser to: https://168.110.210.148:36977/613ccb60/")
print("2. Browser will show 'Your connection is not private'")
print("3. Click 'Advanced' -> 'Proceed to 168.110.210.148 (unsafe)'")
print("4. Login with credentials shown above")
