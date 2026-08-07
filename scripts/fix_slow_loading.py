#!/usr/bin/env python3
"""Find and disable external network calls in aaPanel login page"""
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

# 1. Find ALL URLs and API endpoints in login page
print("[1] All URLs/endpoints in login page...")
out, err, code = run(client, """curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -oE 'https?://[^ "'\''<>]+' | sort -u""")
print(f"  {out}")

# 2. Find all fetch/ajax/request calls  
print("\n[2] AJAX/Fetch calls in login page...")
out, err, code = run(client, """curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -oE "url\s*:\s*'[^']*'" | head -20""")
print(f"  {out}")

# 3. Check for font loading
print("\n[3] Font loading...")
out, err, code = run(client, """curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -iE 'font|@font-face|googleapis|fonts' | head -10""")
print(f"  {out}")

# 4. Check for WebSocket connections
print("\n[4] WebSocket...")
out, err, code = run(client, """curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -iE 'websocket|socket\.io|ws://' | head -10""")
print(f"  {out}")

# 5. Check for setTimeout/setInterval that might cause loading
print("\n[5] Timer/delay code...")
out, err, code = run(client, """curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -c 'setTimeout\|setInterval'""")
print(f"  Timer count: {out}")

# 6. Check aaPanel config for update/phone-home settings
print("\n[6] Check phone-home/update settings...")
configs_to_check = [
    "www/server/panel/data/ntp.pl",
    "www/server/panel/data/https.pl", 
    "www/server/panel/data/close.pl",
    "www/server/panel/data/force.pl",
    "www/server/panel/data/index.pl",
]
for cfg in configs_to_check:
    out, err, code = run(client, f"sudo cat /{cfg} 2>&1")
    if "No such" not in out:
        print(f"  {cfg}: {out}")

# 7. Check config.json for any update/CDN URLs
print("\n[7] Panel config...")
out, err, code = run(client, "sudo cat /www/server/panel/config/config.json 2>&1")
print(f"  {out}")

# 8. Disable update check and external connections
print("\n[8] Disable external connections...")
# Create/modify files to disable update checks
run(client, "echo '0' | sudo tee /www/server/panel/data/ntp.pl 2>/dev/null")
run(client, "echo '0' | sudo tee /www/server/panel/data/auto_update.pl 2>/dev/null")

# Check if there's a way to disable CDN
out, err, code = run(client, "sudo grep -rn 'cdn.aapanel\\|aapanel.com\\|node.aapanel' /www/server/panel/class/public.py 2>/dev/null | head -5")
print(f"  CDN refs: {out}")

# 9. Block external aaPanel connections via hosts file to prevent slow timeouts
print("\n[9] Block aaPanel external domains in hosts file...")
out, err, code = run(client, """sudo bash -c 'cat >> /etc/hosts << EOF
# Block aaPanel phone-home (speed up loading)
127.0.0.1 www.aapanel.com
127.0.0.1 node.aapanel.com
127.0.0.1 api.aapanel.com
127.0.0.1 cdn.aapanel.com
127.0.0.1 download.bt.cn
127.0.0.1 www.bt.cn
EOF' 2>&1""")
print(f"  Hosts updated: code={code}")

# 10. Restart and test
print("\n[10] Restart aaPanel...")
out, err, code = run(client, "sudo bt restart 2>&1")
print(f"  Restart: {out if out else 'done'}")
time.sleep(5)

# 11. Test page load time
print("\n[11] Test page load time...")
out, err, code = run(client, """curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' --connect-timeout 10 -w '\\nHTTP: %{http_code}\\nSize: %{size_download}\\nTime: %{time_total}s\\n' -o /dev/null 2>&1""")
print(f"  {out}")

client.close()
print("\n" + "=" * 60)
print("DONE: External connections blocked via hosts file")
print("Reload page - should be faster now")
print("=" * 60)
