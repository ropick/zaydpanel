#!/usr/bin/env python3
"""Add aaPanel proxy through Docker nginx on /panel/ path with Cloudflare SSL"""
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

# Add a server block in Docker nginx for staging.pro99.my.id:80 
# that proxies /panel/ to aaPanel on host network
# This way user accesses https://staging.pro99.my.id/panel/613ccb60/
# and Cloudflare handles SSL (no self-signed cert warning)

print("[1] Update Docker nginx config to add /panel/ proxy...")

nginx_conf = """server {
    listen 80;
    server_name staging.pro99.my.id 168.110.210.148;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # aaPanel proxy via /panel/ path
    # Access: http://staging.pro99.my.id/panel/613ccb60/
    # Docker nginx -> host 172.17.0.1:36977 (aaPanel HTTPS)
    location /panel/ {
        proxy_pass https://172.17.0.1:36977/;
        proxy_ssl_verify off;
        proxy_set_header Host $host:$server_port;
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

    # aaPanel static files (direct proxy for performance)
    location /panel/static/ {
        proxy_pass https://172.17.0.1:36977/static/;
        proxy_ssl_verify off;
        proxy_set_header Host $host:$server_port;
        proxy_http_version 1.1;
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

cmd = f"""cat > /tmp/nginx_panel.conf << 'NEOF'
{nginx_conf}
NEOF
sudo cp /tmp/nginx_panel.conf /opt/nusahost/deploy/nginx.conf
sudo cat /opt/nusahost/deploy/nginx.conf"""
out, err, code = run(client, cmd)
print(f"  Config updated: code={code}")

# 2. Reload Docker nginx
print("\n[2] Reload Docker nginx...")
out, err, code = run(client, "sudo docker exec nusahost-nginx nginx -t 2>&1")
print(f"  Config test: {out} {err}")
out, err, code = run(client, "sudo docker exec nusahost-nginx nginx -s reload 2>&1")
print(f"  Reload: code={code}")

time.sleep(2)

# 3. Test the /panel/ proxy
print("\n[3] Test /panel/ proxy...")
tests = [
    ("curl -sI 'http://localhost/panel/613ccb60/' -H 'User-Agent: Mozilla/5.0' --connect-timeout 5 2>&1", "Panel via /panel/"),
    ("curl -sI 'http://localhost/panel/613ccb60/' -H 'User-Agent: Mozilla/5.0' -L --connect-timeout 5 2>&1 | head -15", "Panel follow redirect"),
    ("curl -s 'http://localhost/panel/613ccb60/' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' --connect-timeout 5 -w '\\nHTTP: %{http_code} Size: %{size_download} Time: %{time_total}s' -o /dev/null 2>&1", "Panel timing"),
    ("curl -sI 'http://localhost/' --connect-timeout 5 2>&1 | head -5", "Landing page still works"),
]
for cmd, desc in tests:
    out, err, code = run(client, cmd)
    print(f"  [{desc}]: {out[:300]}")

client.close()
print("\n" + "=" * 60)
print("PANEL PROXY CONFIGURED!")
print("Access aaPanel via: https://staging.pro99.my.id/panel/613ccb60/")
print("(Uses Cloudflare SSL - no self-signed cert warning!)")
print("=" * 60)
