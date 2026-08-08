#!/usr/bin/env python3
"""Fix: Disable Secure cookie so session works through HTTP proxy"""
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

# The issue: aaPanel has SSL on, so it sets SESSION_COOKIE_SECURE = True
# When Docker nginx proxies via HTTPS to aaPanel, the cookie gets "Secure" flag
# But the connection between browser->Cloudflare->Docker nginx is HTTPS,
# and Docker nginx->aaPanel is HTTPS (proxy_ssl_verify off)
# The problem might be that the cookie path or domain doesn't match

# Let me check: does /code work when accessed DIRECTLY via aaPanel (not proxy)?
print("[1] Test /code DIRECTLY via aaPanel HTTPS...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/code' --connect-timeout 5 -w '\\nHTTP: %{http_code} Size: %{size_download}' -o /dev/null 2>&1")
print(f"  Direct: {out}")

# Test /code via proxy with cookies
out, err, code = run(client, "curl -s 'http://localhost/code' -H 'Host: panel.pro99.my.id' --connect-timeout 5 -c /tmp/c1.txt -w '\\nHTTP: %{http_code}' 2>&1")
print(f"  Via proxy: {out[:200]}")

# The real issue: /code returns 404 because it's not a valid route
# aaPanel only serves routes under /613ccb60/ or specific API routes
# The login page JS probably constructs URLs relative to root
# But those routes exist at root level on aaPanel

# Wait - let me check the actual aaPanel routes
print("\n[2] Check if /code route exists in aaPanel...")
out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/code' -o /dev/null -w '%{http_code}' 2>&1")
print(f"  /code direct: {out}")

out, err, code = run(client, "curl -sk 'https://127.0.0.1:36977/static/js/md5.js' -o /dev/null -w '%{http_code}' 2>&1")
print(f"  /static direct: {out}")

# Check if maybe the issue is Cloudflare
# Cloudflare might be blocking or modifying the requests
# Let's check the Docker nginx logs for the user's actual requests

print("\n[3] Docker nginx access log (user requests)...")
out, err, code = run(client, "sudo docker logs nusahost-nginx --tail 30 2>&1 | grep -v 'curl'")
print(f"  {out[:1500]}")

# Check if /code is being called from the browser
out, err, code = run(client, "sudo docker logs nusahost-nginx --tail 50 2>&1 | grep '/code\\|/userLang'")
print(f"\n  /code and /userLang calls:\n{out[:500]}")

# 4. The REAL fix: check if maybe Cloudflare is interfering
# Cloudflare might have WAF rules blocking POST requests
# Or Cloudflare might be stripping cookies

# 5. Actually, let me check: does the page load but just show blank/spinner?
# The user said "loading" - let me check if there's JS error
# The login page has inline JS - if one JS file fails, the whole page breaks

# 6. Let me check what JS the page actually needs
print("\n[4] Check JS references in page...")
out, err, code = run(client, """curl -s 'http://localhost/613ccb60/' -H 'Host: panel.pro99.my.id' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -oE '<script[^>]+src="[^"]+"' | head -10""")
print(f"  {out}")

# 7. Check if there's a specific JS that loads the login form
print("\n[5] Check page bottom for form rendering...")
out, err, code = run(client, """curl -s 'http://localhost/613ccb60/' -H 'Host: panel.pro99.my.id' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -iE '<form|<input|<button|type="password"|type="submit"' | head -10""")
print(f"  Form elements: {out}")

# 8. The page might be a Vue app that renders client-side
# Check for Vue/React mount point
out, err, code = run(client, """curl -s 'http://localhost/613ccb60/' -H 'Host: panel.pro99.my.id' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -oE 'id="[^"]*app[^"]*"|id="[^"]*root[^"]*"|id="[^"]*login[^"]*"' | head -5""")
print(f"\n  App mount points: {out}")

client.close()
