#!/usr/bin/env python3
"""Fix static asset paths - proxy /static/ and fix Host header"""
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

# The problem: aaPanel generates HTML with /static/ paths.
# When accessed via /panel/, browser requests /static/ which goes to Next.js (404).
# Fix: Add /static/ proxy AND keep /panel/static/ for subrequests.
# Also fix the Host header to use 168.110.210.148:36977 so aaPanel generates correct internal URLs.

print("[1] Update nginx config with /static/ proxy...")

nginx_conf = """server {
    listen 80;
    server_name staging.pro99.my.id 168.110.210.148;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Proxy ALL aaPanel traffic to internal port 36977
    # Match: /panel/, /static/, /favicon.ico
    location /panel/ {
        proxy_pass https://172.17.0.1:36977/;
        proxy_ssl_verify off;
        proxy_set_header Host 168.110.210.148:36977;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_buffering off;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        # Sub-filter to rewrite /static/ to /panel/static/ in HTML
        sub_filter_once off;
        sub_filter_types text/html application/javascript text/css;
        sub_filter 'href="/static/' 'href="/panel/static/';
        sub_filter 'src="/static/' 'src="/panel/static/';
        sub_filter "'/static/" "'/panel/static/";
        sub_filter '"/static/' '"/panel/static/';
    }

    # Also proxy /static/ directly for aaPanel assets (in case of direct refs)
    location /static/ {
        proxy_pass https://172.17.0.1:36977/static/;
        proxy_ssl_verify off;
        proxy_set_header Host 168.110.210.148:36977;
        proxy_http_version 1.1;
        proxy_connect_timeout 60s;
    }

    # Reverse proxy to Next.js app (everything else)
    location / {
        proxy_pass http://app:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
"""

cmd = f"""cat > /tmp/nginx_fix.conf << 'NEOF'
{nginx_conf}
NEOF
sudo cp /tmp/nginx_fix.conf /opt/nusahost/deploy/nginx.conf"""
out, err, code = run(client, cmd)
print(f"  Config updated: code={code}")

# 2. Reload Docker nginx
print("\n[2] Reload Docker nginx...")
out, err, code = run(client, "sudo docker exec nusahost-nginx nginx -t 2>&1")
print(f"  Config test: {out} {err}")
if "successful" in out:
    out, err, code = run(client, "sudo docker exec nusahost-nginx nginx -s reload 2>&1")
    print(f"  Reload: code={code}")
else:
    # Config test failed - might need headers-more module for sub_filter
    print("  sub_filter might need nginx rebuild, trying alternative...")

time.sleep(2)

# 3. Test
print("\n[3] Test static paths...")
tests = [
    ("curl -sI 'http://localhost/static/js/md5.js' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1", "/static/js/md5.js"),
    ("curl -sI 'http://localhost/static/vite/favicon.ico' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1", "/static/vite/favicon.ico"),
    ("curl -sI 'http://localhost/panel/static/js/md5.js' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1", "/panel/static/js/md5.js"),
    ("curl -s 'http://localhost/panel/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 -w '\\nHTTP: %{http_code} Size: %{size_download}' -o /dev/null 2>&1", "Login page"),
    ("curl -sI 'http://localhost/' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1", "Landing page"),
]
for t, desc in tests:
    out, _, _ = run(client, t)
    print(f"  {desc}: {out}")

# 4. Check if sub_filter worked
print("\n[4] Check if sub_filter rewrote paths...")
out, err, code = run(client, """curl -s 'http://localhost/panel/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -c '/panel/static/'""")
print(f"  /panel/static/ refs: {out}")

out, err, code = run(client, """curl -s 'http://localhost/panel/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -c 'src="/static/'""")
print(f"  /static/ (unrewritten) refs: {out}")

client.close()
