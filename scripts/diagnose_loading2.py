#!/usr/bin/env python3
"""Deep diagnose loading issue on panel.pro99.my.id"""
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

# 1. Check aaPanel error log
print("[1] aaPanel error log...")
out, err, code = run(client, "sudo tail -30 /www/server/panel/logs/error.log 2>&1")
print(f"  {out[:1500] if out else 'CLEAN'}")

# 2. Test /code endpoint (captcha)
print("\n[2] Test /code endpoint...")
out, err, code = run(client, "curl -sv 'http://localhost/code' -H 'Host: panel.pro99.my.id' --connect-timeout 5 2>&1 | tail -10")
print(f"  {out}")

# 3. Test /userLang endpoint
print("\n[3] Test /userLang endpoint...")
out, err, code = run(client, "curl -s 'http://localhost/userLang?action=get_language' -H 'Host: panel.pro99.my.id' -X POST --connect-timeout 5 -w '\\nHTTP: %{http_code}' 2>&1")
print(f"  {out[:500]}")

# 4. Test with cookies (session from login page)
print("\n[4] Get login page with cookies and test APIs...")
out, err, code = run(client, "curl -sv 'http://localhost/613ccb60/' -H 'Host: panel.pro99.my.id' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' --connect-timeout 5 -c /tmp/panel_cookies.txt 2>&1 | grep -i 'set-cookie'")
print(f"  Cookies set: {out}")

# 5. Use those cookies to test /code
out, err, code = run(client, "curl -s 'http://localhost/code' -H 'Host: panel.pro99.my.id' -b /tmp/panel_cookies.txt --connect-timeout 5 -w '\\nHTTP: %{http_code} Size: %{size_download}' -o /dev/null 2>&1")
print(f"\n  /code with cookies: {out}")

out, err, code = run(client, "curl -s 'http://localhost/userLang?action=get_language' -H 'Host: panel.pro99.my.id' -b /tmp/panel_cookies.txt -X POST --connect-timeout 5 -w '\\nHTTP: %{http_code}' 2>&1")
print(f"  /userLang with cookies: {out[:300]}")

# 6. Check the Docker nginx error log
print("\n[5] Docker nginx error log...")
out, err, code = run(client, "sudo docker logs nusahost-nginx --tail 10 2>&1")
print(f"  {out}")

# 7. Check aaPanel webserver log
print("\n[6] aaPanel webserver log...")
out, err, code = run(client, "sudo cat /www/server/panel/webserver/logs/webserver.log 2>&1 | tail -20")
print(f"  {out[:500] if out else 'empty'}")

# 8. Check if the page content has a loading overlay
print("\n[7] Check for loading overlay in page HTML...")
out, err, code = run(client, """curl -s 'http://localhost/613ccb60/' -H 'Host: panel.pro99.my.id' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -oiE 'loading|wait|spinner|mask|overlay|<div class="[^"]*load[^"]*"' | head -10""")
print(f"  Loading elements: {out}")

# 9. Check if the page has an onload handler
print("\n[8] Check window.onload handler...")
out, err, code = run(client, """curl -s 'http://localhost/613ccb60/' -H 'Host: panel.pro99.my.id' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -A5 'window.onload' | head -20""")
print(f"  onload: {out[:500]}")

client.close()
