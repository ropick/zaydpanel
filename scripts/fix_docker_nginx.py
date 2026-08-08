#!/usr/bin/env python3
"""Fix: Restore Docker nginx to handle port 80/443 (bypass Oracle Security List issue)"""
import paramiko, time

def connect():
    key = paramiko.RSAKey.from_private_key_file("/home/z/my-project/deploy/nusahost_id")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

print("=" * 60)
print("FIX: Restore Docker nginx (proven to work externally)")
print("=" * 60)

client = connect()

# Step 1: Stop system nginx to free port 80/443
print("\n[1] Stop system nginx...")
out, err, code = run(client, "sudo systemctl stop nginx && sudo systemctl disable nginx 2>&1")
print(f"  nginx stopped: code={code}")

# Step 2: Update Docker nginx config to also handle aaPanel port
print("\n[2] Update Docker nginx config...")

nginx_conf = """server {
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

# aaPanel reverse proxy (accessible via /panel path or port)
server {
    listen 36977;
    server_name 168.110.210.148;

    location / {
        proxy_pass http://172.17.0.1:36977;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
"""

cmd = f"""cat > /tmp/nginx_proxy.conf << 'NEOF'
{nginx_conf}
NEOF
sudo cp /tmp/nginx_proxy.conf /opt/nusahost/deploy/nginx.conf
sudo cat /opt/nusahost/deploy/nginx.conf
"""
out, err, code = run(client, cmd, timeout=15)
print(f"  Config updated: code={code}")

# Step 3: Restart Docker containers (nginx + certbot, app should already be running)
print("\n[3] Restart Docker containers...")
out, err, code = run(client, "cd /opt/nusahost/deploy && sudo docker compose down 2>&1", timeout=60)
print(f"  compose down: code={code}")

time.sleep(3)

out, err, code = run(client, "cd /opt/nusahost/deploy && sudo docker compose up -d 2>&1", timeout=120)
print(f"  compose up: code={code}")
if out:
    print(f"  {out}")

time.sleep(5)

# Step 4: Verify
print("\n[4] Verification...")
tests = [
    ("ss -tlnp | grep -E ':(80|3000|443|36977) '", "Ports"),
    ("sudo docker ps --format '{{.Names}} {{.Status}} {{.Ports}}'", "Docker"),
    ("curl -s -o /dev/null -w '%{http_code}' http://localhost:80", "Nginx (80)"),
    ("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000", "App (3000)"),
    ("curl -s -o /dev/null -w '%{http_code}' http://localhost:36977", "Panel via Docker (36977)"),
    ("sudo bt status 2>/dev/null", "aaPanel"),
    ("sudo docker logs nusahost-nginx --tail 5 2>&1", "Nginx logs"),
]

for cmd, desc in tests:
    out, _, _ = run(client, cmd, timeout=15)
    print(f"  {desc}: {out[:200] if out else 'N/A'}")

client.close()
print("\n" + "=" * 60)
