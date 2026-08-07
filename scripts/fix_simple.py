#!/usr/bin/env python3
"""Fix login page 404 - simplify nginx config"""
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

print("[1] Simplify nginx config...")

# Simple approach: just proxy /panel/ and /static/ to aaPanel
# Don't mess with sub_filter - keep it clean
nginx_conf = """server {
    listen 80;
    server_name staging.pro99.my.id 168.110.210.148;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # aaPanel static assets (proxy directly)
    location /static/ {
        proxy_pass https://172.17.0.1:36977/static/;
        proxy_ssl_verify off;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_connect_timeout 60s;
        proxy_read_timeout 300s;
    }

    # aaPanel proxy via /panel/ path
    location /panel/ {
        proxy_pass https://172.17.0.1:36977/;
        proxy_ssl_verify off;
        proxy_set_header Host $host;
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
    }

    # Reverse proxy to Next.js app
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

cmd = f"""cat > /tmp/nginx_simple.conf << 'NEOF'
{nginx_conf}
NEOF
sudo cp /tmp/nginx_simple.conf /opt/nusahost/deploy/nginx.conf"""
out, err, code = run(client, cmd)
print(f"  Config updated: code={code}")

# 2. Reload
print("\n[2] Reload Docker nginx...")
out, err, code = run(client, "sudo docker exec nusahost-nginx nginx -t 2>&1")
print(f"  Test: {out} {err}")
out, err, code = run(client, "sudo docker exec nusahost-nginx nginx -s reload 2>&1")
print(f"  Reload: code={code}")
time.sleep(2)

# 3. Test everything
print("\n[3] Test all paths...")
tests = [
    ("curl -sI 'http://localhost/panel/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | head -5", "Login page HEAD"),
    ("curl -s 'http://localhost/panel/613ccb60/' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' --connect-timeout 5 -w 'HTTP: %{http_code} Size: %{size_download}' -o /dev/null 2>&1", "Login page GET"),
    ("curl -sI 'http://localhost/static/js/md5.js' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1", "/static/js/md5.js"),
    ("curl -sI 'http://localhost/static/vite/favicon.ico' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1", "/static/vite/favicon.ico"),
    ("curl -sI 'http://localhost/' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1", "Landing page"),
]
for t, desc in tests:
    out, _, _ = run(client, t)
    print(f"  {desc}: {out}")

# 4. Check what HTML the login page returns
print("\n[4] Check login page HTML...")
out, err, code = run(client, """curl -s 'http://localhost/panel/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | grep -oE '(src|href)="[^"]*"' | head -15""")
print(f"  Asset refs: {out}")

client.close()
