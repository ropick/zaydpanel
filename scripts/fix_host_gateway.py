#!/usr/bin/env python3
"""Fix 502 - use 172.17.0.1 (host gateway) instead of 127.0.0.1"""
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

# Fix: 127.0.0.1 inside Docker = container localhost, NOT host
# Must use 172.17.0.1 = docker0 bridge = host machine
print("[1] Fix proxy_pass to use 172.17.0.1...")

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

    # Proxy EVERYTHING to aaPanel on host
    location / {
        proxy_pass https://172.17.0.1:36977;
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

cmd = f"""cat > /tmp/nginx_host.conf << 'NEOF'
{nginx_conf}
NEOF
sudo cp /tmp/nginx_host.conf /opt/nusahost/deploy/nginx.conf"""
out, err, code = run(client, cmd)
print(f"  Config updated: code={code}")

# 2. Reload
print("\n[2] Reload Docker nginx...")
run(client, "sudo docker exec nusahost-nginx nginx -s reload 2>&1")
time.sleep(2)

# 3. Test
print("\n[3] Test panel.pro99.my.id via 172.17.0.1...")
tests = [
    ("curl -s 'http://localhost/613ccb60/' -H 'Host: panel.pro99.my.id' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' --connect-timeout 5 -w '\\nHTTP: %{http_code} Size: %{size_download} Time: %{time_total}s' -o /dev/null 2>&1", "Login page"),
    ("curl -sI 'http://localhost/static/js/md5.js' -H 'Host: panel.pro99.my.id' --connect-timeout 3 -o /dev/null -w '%{http_code}' 2>&1", "/static/js/md5.js"),
    ("curl -s 'http://localhost/code' -H 'Host: panel.pro99.my.id' --connect-timeout 3 -w '\\n%{http_code}' 2>&1", "/code API"),
    ("curl -s 'http://localhost/' -H 'Host: staging.pro99.my.id' --connect-timeout 3 -w '%{http_code}' 2>&1", "Landing page"),
]
for t, desc in tests:
    out, _, _ = run(client, t)
    print(f"  {desc}: {out}")

client.close()
