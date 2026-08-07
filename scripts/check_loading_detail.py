#!/usr/bin/env python3
"""Check static/js files and full login page loading"""
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

# 1. Check /static/js/ directory
print("[1] /static/js/ files...")
out, err, code = run(client, "sudo ls /www/server/panel/BTPanel/static/js/ 2>&1")
print(f"  {out}")

# 2. Test specific JS files that login page needs
print("\n[2] Test JS file access...")
js_files = [
    "/static/js/md5.js",
    "/static/js/qrcode.min.js",
    "/static/js/jsencrypt.min.js",
    "/static/js/i18next.min.js",
]
for f in js_files:
    out, err, code = run(client, f"curl -sk 'https://127.0.0.1:36977{f}' --connect-timeout 5 -o /dev/null -w '%{{http_code}} size=%{{size_download}}' 2>&1")
    print(f"  {f}: {out}")

# 3. Get the FULL login page HTML to understand the loading flow
print("\n[3] Full login page scripts section...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -E '<script|</script>|<link.*css|import|vue|react|createApp' | head -30")
print(f"  {out}")

# 4. Check for Vue/React app initialization in login page
print("\n[4] Check for app mount/init...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -oE 'createApp|mount\(|#app|vue|React|ReactDOM|render\(' | head -10")
print(f"  {out}")

# 5. Check the bottom part of login template for JS loading
print("\n[5] Bottom of login template (last 100 lines)...")
out, err, code = run(client, "sudo tail -100 /www/server/panel/BTPanel/templates/default/login.html 2>&1")
print(out[:3000])

# 6. Check the full login page from the server - look for any CDN references
print("\n[6] Check for external URLs in login page...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -oE 'https?://[^ \"'\'']+' | sort -u")
print(f"  External URLs: {out}")

client.close()
