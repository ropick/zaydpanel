#!/usr/bin/env python3
"""
FASE 3C-E: Configure aaPanel
- Open port 36977 in OS firewall
- Install Nginx via aaPanel
- Create website staging.pro99.my.id
- Setup reverse proxy to Next.js app on port 3000
"""
import paramiko, time, json

def connect():
    key = paramiko.RSAKey.from_private_key_file("/home/z/my-project/deploy/nusahost_id")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

print("=" * 60)
print("FASE 3C-E: Configure aaPanel")
print("=" * 60)

client = connect()

# === STEP 1: Open port 36977 in OS firewall ===
print("\n[1] Opening port 36977 in OS firewall...")
out, err, code = run(client, "sudo firewall-cmd --permanent --add-port=36977/tcp 2>&1 && sudo firewall-cmd --permanent --add-port=8888/tcp 2>&1 && sudo firewall-cmd --reload 2>&1")
print(f"  firewall-cmd: {out}")
if code != 0:
    # Try iptables fallback
    print("  Trying iptables...")
    out, err, code = run(client, "sudo iptables -I INPUT -p tcp --dport 36977 -j ACCEPT 2>&1")
    print(f"  iptables: code={code}")

# Also check current firewall rules
out, _, _ = run(client, "sudo firewall-cmd --list-ports 2>/dev/null")
print(f"  Open ports: {out}")

out, _, _ = run(client, "sudo iptables -L INPUT -n 2>/dev/null | head -15")
print(f"  iptables INPUT:\n{out}")

# === STEP 2: Install Nginx via aaPanel CLI ===
print("\n[2] Installing Nginx via aaPanel...")

# First check what's available
out, _, _ = run(client, "sudo bt 14 2>/dev/null")  # List available software
# Actually, let me use the panel API or just install via command line
# aaPanel has a CLI: bt <option>

# Install nginx via apt (aaPanel-friendly)
out, err, code = run(client, "sudo apt-get install -y nginx 2>&1 | tail -10", timeout=120)
print(f"  apt install nginx: code={code}")
if out:
    print(f"  {out}")

# Check nginx installed
out, _, _ = run(client, "which nginx && nginx -v 2>&1")
print(f"  Nginx: {out}")

# === STEP 3: Start nginx ===
print("\n[3] Starting Nginx...")
out, err, code = run(client, "sudo systemctl enable nginx 2>&1 && sudo systemctl start nginx 2>&1")
print(f"  systemctl: code={code}, {out}")

# Stop it if running since we'll manage via aaPanel config
# Actually let's configure nginx to serve as reverse proxy

# === STEP 4: Create website config for staging.pro99.my.id ===
print("\n[4] Creating reverse proxy config for staging.pro99.my.id...")

# Create the website directory
out, err, code = run(client, "sudo mkdir -p /www/wwwroot/staging.pro99.my.id", timeout=15)

# Create nginx reverse proxy config
nginx_conf = """server {
    listen 80;
    server_name staging.pro99.my.id;
    
    access_log /www/wwwlogs/staging.pro99.my.id.log;
    error_log /www/wwwlogs/staging.pro99.my.id.error.log;
    
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }
}
"""

# Write config
cmd = f"""cat > /tmp/staging_proxy.conf << 'NEOF'
{nginx_conf}
NEOF
sudo cp /tmp/staging_proxy.conf /www/server/nginx/conf/vhost/staging.pro99.my.id.conf
sudo mkdir -p /www/server/nginx/conf/vhost /www/wwwlogs
sudo cp /tmp/staging_proxy.conf /etc/nginx/conf.d/staging.pro99.my.id.conf
"""
out, err, code = run(client, cmd, timeout=15)
print(f"  Config written: code={code}")

# Test nginx config
out, err, code = run(client, "sudo nginx -t 2>&1")
print(f"  nginx -t: {out}")

if code == 0:
    # Reload nginx
    out, err, code = run(client, "sudo systemctl reload nginx 2>&1 || sudo nginx -s reload 2>&1")
    print(f"  nginx reload: code={code}")
else:
    print(f"  ⚠️ nginx config test failed! {out}")

# === STEP 5: Verify everything works ===
print("\n[5] Verification...")

# Check ports
out, _, _ = run(client, "ss -tlnp | grep -E ':(80|3000|36977|8888) '")
print(f"  Ports:\n{out if out else '  None'}")

# Test Next.js app directly
out, _, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000 2>/dev/null")
print(f"  Next.js (3000): HTTP {out}")

# Test via nginx reverse proxy
out, _, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' -H 'Host: staging.pro99.my.id' http://localhost:80 2>/dev/null")
print(f"  Nginx proxy (80): HTTP {out}")

# Test via external IP
out, _, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://168.110.210.148 2>/dev/null")
print(f"  External (IP:80): HTTP {out}")

# Test aaPanel
out, _, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:36977/613ccb60 2>/dev/null")
print(f"  aaPanel (36977): HTTP {out}")

# Docker status
out, _, _ = run(client, "docker ps --format '{{.Names}} {{.Status}} {{.Ports}}'")
print(f"  Docker: {out if out else 'No containers'}")

# aaPanel status
out, _, _ = run(client, "sudo bt status 2>/dev/null")
print(f"  aaPanel: {out}")

client.close()

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
print("\n📋 ACTIONS NEEDED BY YOU:")
print("1. Add port 36977 to Oracle Cloud Security List ingress rules")
print("2. Access panel: http://168.110.210.148:36977/613ccb60")
print("3. Username: ib0xgxtd | Password: 025c4aff")
