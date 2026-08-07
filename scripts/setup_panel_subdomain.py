#!/usr/bin/env python3
"""Setup panel.pro99.my.id as dedicated subdomain for aaPanel"""
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

print("[1] Update Docker nginx config with panel.pro99.my.id...")

# panel.pro99.my.id on port 80 -> proxy ALL to aaPanel
# This way all API paths (/code, /userLang, /login etc) work correctly
# because the ENTIRE domain is dedicated to aaPanel
nginx_conf = """# ============================================
# aaPanel - dedicated subdomain
# ============================================
server {
    listen 80;
    server_name panel.pro99.my.id;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Proxy EVERYTHING to aaPanel
    location / {
        proxy_pass https://127.0.0.1:36977;
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
}

# ============================================
# Landing page - staging subdomain
# ============================================
server {
    listen 80;
    server_name staging.pro99.my.id 168.110.210.148;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
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

cmd = f"""cat > /tmp/nginx_final.conf << 'NEOF'
{nginx_conf}
NEOF
sudo cp /tmp/nginx_final.conf /opt/nusahost/deploy/nginx.conf"""
out, err, code = run(client, cmd)
print(f"  Config updated: code={code}")

# 2. Reload
print("\n[2] Reload Docker nginx...")
out, err, code = run(client, "sudo docker exec nusahost-nginx nginx -t 2>&1")
print(f"  Test: {out} {err}")
out, err, code = run(client, "sudo docker exec nusahost-nginx nginx -s reload 2>&1")
print(f"  Reload: code={code}")
time.sleep(2)

# 3. Test via panel.pro99.my.id
print("\n[3] Test panel.pro99.my.id...")
tests = [
    ("curl -sI 'http://localhost/' -H 'Host: panel.pro99.my.id' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | head -8", "Panel root (should be 404)"),
    ("curl -sI 'http://localhost/613ccb60/' -H 'Host: panel.pro99.my.id' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1 | head -8", "Panel security path"),
    ("curl -s 'http://localhost/613ccb60/' -H 'Host: panel.pro99.my.id' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' --connect-timeout 5 -w '\\nHTTP: %{http_code} Size: %{size_download} Time: %{time_total}s' -o /dev/null 2>&1", "Login page timing"),
    ("curl -sI 'http://localhost/static/js/md5.js' -H 'Host: panel.pro99.my.id' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1", "/static/js/md5.js"),
    ("curl -sI 'http://localhost/' -H 'Host: staging.pro99.my.id' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1", "Landing page (staging)"),
]
for t, desc in tests:
    out, _, _ = run(client, t)
    print(f"  {desc}: {out}")

# 4. Check if API paths work
print("\n[4] Test API paths via panel.pro99.my.id...")
api_tests = [
    ("curl -s 'http://localhost/code' -H 'Host: panel.pro99.my.id' --connect-timeout 3 -w '\\n%{http_code}' 2>&1", "/code"),
    ("curl -s 'http://localhost/userLang?action=get_language' -H 'Host: panel.pro99.my.id' -X POST --connect-timeout 3 -w '\\n%{http_code}' 2>&1", "/userLang"),
]
for t, desc in api_tests:
    out, _, _ = run(client, t)
    print(f"  {desc}: {out[:200]}")

client.close()
print("\n" + "=" * 60)
print("DONE! Access aaPanel at:")
print("https://panel.pro99.my.id/613ccb60/")
print("=" * 60)
