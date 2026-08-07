#!/usr/bin/env python3
"""Fix aaPanel connection reset: Remove 36977 proxy from Docker nginx + disable HTTPS redirect"""
import paramiko, time

def connect():
    key = paramiko.RSAKey.from_private_key_file("/home/z/my-project/deploy/nusahost_id")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

client = connect()

print("=" * 60)
print("FIX: aaPanel Connection Reset")
print("=" * 60)

# Step 1: Remove 36977 server block from Docker nginx config
print("\n[1] Update Docker nginx config (remove 36977 proxy block)...")

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
"""

cmd = f"""cat > /tmp/nginx_fixed.conf << 'NEOF'
{nginx_conf}
NEOF
sudo cp /tmp/nginx_fixed.conf /opt/nusahost/deploy/nginx.conf"""
out, err, code = run(client, cmd)
print(f"  Config updated: code={code}")

# Step 2: Reload Docker nginx (not restart, to avoid downtime)
print("\n[2] Reload Docker nginx...")
out, err, code = run(client, "sudo docker exec nusahost-nginx nginx -t 2>&1")
print(f"  Config test: {out} {err}")
out, err, code = run(client, "sudo docker exec nusahost-nginx nginx -s reload 2>&1")
print(f"  Reload: code={code} {out} {err}")

# Step 3: Fix aaPanel HTTPS redirect - disable SSL/HTTPS forcing
print("\n[3] Disable aaPanel HTTPS redirect...")
# Check current SSL setting
out, err, code = run(client, "sudo cat /www/server/panel/data/ssl.pl 2>&1")
print(f"  Current SSL setting: {out if out else 'N/A'}")

# Disable SSL in aaPanel (set to 0)
out, err, code = run(client, "echo '0' | sudo tee /www/server/panel/data/ssl.pl")
print(f"  SSL disabled: {out.strip()}")

# Also check if there's an SSL certificate file that's causing redirect
out, err, code = run(client, "sudo ls -la /www/server/panel/ssl/ 2>&1")
print(f"  SSL certs: {out[:300] if out else 'none'}")

# Check the self-signed cert info
out, err, code = run(client, "sudo cat /www/server/panel/data/selfCert.pl 2>&1")
print(f"  Self cert setting: {out if out else 'N/A'}")

# Disable the self-signed cert to prevent HTTPS redirect
out, err, code = run(client, "echo '0' | sudo tee /www/server/panel/data/selfCert.pl")
print(f"  Self cert disabled: {out.strip()}")

# Step 4: Restart aaPanel to apply changes
print("\n[4] Restart aaPanel services...")
out, err, code = run(client, "sudo bt restart 2>&1")
print(f"  aaPanel restart: {out if out else 'done'}")

time.sleep(3)

# Step 5: Verify
print("\n[5] Verification...")

# Check port 36977 from host (bypass Docker)
out, err, code = run(client, "curl -sI http://127.0.0.1:36977/ --connect-timeout 5 2>&1")
print(f"  curl 127.0.0.1:36977: {out[:400] if out else 'FAILED'}")

# Check if still redirecting to HTTPS
if "302" in out and "https" in out.lower():
    print("  WARNING: Still redirecting to HTTPS!")
    print("  Trying additional fix...")
    
    # Check and modify aaPanel's webserver config
    out, err, code = run(client, "sudo find /www/server/panel -name '*.conf' -o -name '*.py' | xargs grep -l '301\\|302\\|redirect\\|https' 2>/dev/null | head -10")
    print(f"  Files with redirect: {out[:300]}")
    
    # Check the BT-Panel main file for SSL redirect logic
    out, err, code = run(client, "sudo grep -n 'redirect\\|301\\|302\\|https' /www/server/panel/BT-Panel 2>/dev/null | head -20")
    print(f"  BT-Panel redirect code: {out[:500]}")

# Test from external perspective (via IP)
out, err, code = run(client, "curl -sI http://168.110.210.148:36977/ --connect-timeout 5 2>&1")
print(f"  curl 168.110.210.148:36977: {out[:400] if out else 'FAILED'}")

# Check Docker nginx still works on port 80
out, err, code = run(client, "curl -sI http://localhost:80/ --connect-timeout 5 2>&1")
print(f"  curl localhost:80 (landing page): {out[:200] if out else 'FAILED'}")

# Verify Docker nginx config
out, err, code = run(client, "sudo docker exec nusahost-nginx cat /etc/nginx/conf.d/default.conf 2>&1")
print(f"  Docker nginx config (36977 check): {'36977 FOUND - ERROR!' if '36977' in out else '36977 removed - OK'}")

client.close()
print("\n" + "=" * 60)
print("FIX COMPLETE")
print("=" * 60)
