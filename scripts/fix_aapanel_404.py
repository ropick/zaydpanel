#!/usr/bin/env python3
"""Test aaPanel access with security path and fix 404"""
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
print("FIX: aaPanel 404 + Security Path Test")
print("=" * 60)

# Step 1: Get aaPanel info (default username, port, security path)
print("\n[1] Get aaPanel default info...")
out, err, code = run(client, "sudo bt default 2>&1")
print(f"  aaPanel info:\n{out}")

# Step 2: Check aaPanel logs for errors
print("\n[2] aaPanel error logs...")
out, err, code = run(client, "sudo tail -30 /www/server/panel/logs/error.log 2>&1")
print(f"  Error log:\n{out[:800] if out else 'N/A'}")

# Step 3: Check if panel is fully started
print("\n[3] Panel process status...")
out, err, code = run(client, "ps aux | grep -E '(BT-Panel|webserver)' | grep -v grep")
print(f"  Processes:\n{out}")

# Step 4: Wait and test with security path
print("\n[4] Test with security path...")
# The security path from install was /613ccb60
# aaPanel URL format: http://IP:PORT/SECURITY_PATH/
tests = [
    "curl -sI http://127.0.0.1:36977/ --connect-timeout 5 2>&1",
    "curl -sI 'http://127.0.0.1:36977/613ccb60/' --connect-timeout 5 2>&1",
    "curl -sL http://127.0.0.1:36977/ --connect-timeout 5 2>&1 | head -30",
    "curl -sL 'http://127.0.0.1:36977/613ccb60/' --connect-timeout 5 2>&1 | head -30",
]
for cmd in tests:
    out, err, code = run(client, cmd)
    short_cmd = cmd.split("curl -s")[1][:50]
    print(f"  {short_cmd}:")
    print(f"    {out[:300]}")

# Step 5: Check if ssl.pl was recreated
print("\n[5] Check ssl.pl status...")
out, err, code = run(client, "sudo ls -la /www/server/panel/data/ssl.pl 2>&1")
print(f"  ssl.pl: {out if out else 'DOES NOT EXIST'}")

# Step 6: Check the BTPanel app.py for SSL config logic
print("\n[6] SSL config logic in app.py...")
out, err, code = run(client, "sudo grep -A5 -B5 \"app.config\\['SSL'\\]\" /www/server/panel/BTPanel/app.py 2>&1")
print(f"  SSL config:\n{out[:600]}")

# Step 7: Check if the issue is that ssl.pl doesn't exist so it crashes
# The code says: app.config['SSL'] = os.path.exists('data/ssl.pl')
# If ssl.pl doesn't exist, SSL = False, which is what we want
# But maybe it crashed on startup because cert files are missing
print("\n[7] Check panel startup log...")
out, err, code = run(client, "sudo tail -20 /tmp/panelBoot.pl 2>&1")
print(f"  Boot log: {out[:500] if out else 'N/A'}")

out, err, code = run(client, "sudo journalctl -u bt --no-pager -n 20 2>&1")
print(f"  Journal: {out[:500] if out else 'N/A'}")

# Step 8: Test the webserver directly (the webserver binary handles SSL, not Python)
print("\n[8] Check webserver binary config...")
out, err, code = run(client, "sudo find /www/server/panel -name 'webserver*' -type f 2>/dev/null")
print(f"  webserver files: {out[:300]}")

# The webserver binary generates its config from templates
# Since we removed the cert files, it might be generating a broken config
out, err, code = run(client, "sudo ls -la /www/server/panel/ssl/ 2>&1")
print(f"  SSL dir: {out}")

# Let's restore the cert files so webserver doesn't crash, but keep ssl.pl absent
print("\n[9] Restore cert files (keep ssl.pl disabled)...")
out, err, code = run(client, "sudo mv /www/server/panel/ssl/certificate.pem.bak /www/server/panel/ssl/certificate.pem 2>&1")
print(f"  Restore cert: {out if out else 'done'}")
out, err, code = run(client, "sudo mv /www/server/panel/ssl/privateKey.pem.bak /www/server/panel/ssl/privateKey.pem 2>&1")
print(f"  Restore key: {out if out else 'done'}")

# Step 10: Make sure ssl.pl does NOT exist (SSL disabled)
print("\n[10] Ensure ssl.pl is removed (SSL disabled)...")
out, err, code = run(client, "sudo rm -f /www/server/panel/data/ssl.pl 2>&1")
print(f"  ssl.pl removed: code={code}")

# Step 11: Restart aaPanel
print("\n[11] Restart aaPanel...")
out, err, code = run(client, "sudo bt restart 2>&1")
print(f"  Restart: {out if out else 'done'}")

time.sleep(5)

# Step 12: Final test
print("\n[12] FINAL TEST...")
out, err, code = run(client, "curl -sI http://127.0.0.1:36977/ --connect-timeout 5 2>&1")
print(f"  Root path: {out[:400]}")

out, err, code = run(client, "curl -sI 'http://127.0.0.1:36977/613ccb60/' --connect-timeout 5 2>&1")
print(f"  Security path: {out[:400]}")

out, err, code = run(client, "curl -sL 'http://127.0.0.1:36977/613ccb60/' --connect-timeout 5 2>&1 | head -5")
print(f"  Security path body: {out[:300]}")

# External test
out, err, code = run(client, "curl -sI http://168.110.210.148:36977/ --connect-timeout 5 2>&1")
print(f"  External IP: {out[:400]}")

client.close()
print("\n" + "=" * 60)
