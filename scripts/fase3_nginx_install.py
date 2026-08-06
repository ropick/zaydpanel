#!/usr/bin/env python3
"""Install Nginx bypassing aaPanel exclude, configure reverse proxy"""
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
print("Install Nginx + Configure Reverse Proxy")
print("=" * 60)

client = connect()

# Step 1: Temporarily remove nginx from exclude, install, add back
print("\n[1] Install Nginx (bypassing exclude)...")

cmds = [
    # Backup dnf.conf
    "sudo cp /etc/dnf/dnf.conf /etc/dnf/dnf.conf.bak",
    # Remove nginx from exclude line
    "sudo sed -i 's/exclude=httpd nginx/exclude=httpd/' /etc/dnf/dnf.conf",
    # Verify
    "sudo grep exclude /etc/dnf/dnf.conf",
]

for cmd in cmds:
    out, err, code = run(client, cmd, timeout=15)
    if 'exclude' in cmd:
        print(f"  dnf.conf exclude: {out}")

# Install nginx
out, err, code = run(client, "sudo dnf install -y nginx 2>&1 | tail -10", timeout=180)
print(f"  dnf install nginx: code={code}")
if out:
    for line in out.split('\n')[-5:]:
        print(f"  {line}")

# Add nginx back to exclude
run(client, "sudo sed -i 's/exclude=httpd/exclude=httpd nginx/' /etc/dnf/dnf.conf", timeout=10)

# Verify nginx
out, _, _ = run(client, "which nginx 2>/dev/null && sudo nginx -v 2>&1")
print(f"  Nginx: {out}")

# Step 2: Create reverse proxy config
print("\n[2] Create reverse proxy config...")

nginx_conf = """server {
    listen 80 default_server;
    server_name staging.pro99.my.id 168.110.210.148;
    
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
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
"""

cmds2 = [
    "sudo mkdir -p /www/wwwlogs",
    f"echo '{nginx_conf}' | sudo tee /etc/nginx/conf.d/staging.conf > /dev/null",
    "sudo rm -f /etc/nginx/conf.d/default.conf",
]
for cmd in cmds2:
    out, err, code = run(client, cmd, timeout=15)

# Step 3: Test and start
print("\n[3] Test and start Nginx...")
out, err, code = run(client, "sudo nginx -t 2>&1")
print(f"  nginx -t: {out}")

if code == 0:
    out, err, code = run(client, "sudo systemctl enable --now nginx 2>&1", timeout=30)
    print(f"  systemctl: code={code}, {out}")
else:
    print(f"  ❌ Config failed: {err}")

# Step 4: Verify
print("\n[4] Verification...")
time.sleep(2)

tests = [
    ("ss -tlnp | grep ':80 '", "Port 80"),
    ("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000", "Next.js (3000)"),
    ("curl -s -o /dev/null -w '%{http_code}' http://localhost:80", "Nginx (80)"),
    ("curl -s -o /dev/null -w '%{http_code}' http://168.110.210.148", "External (IP)"),
    ("docker ps --format '{{.Names}} {{.Status}}'", "Docker"),
    ("sudo bt status 2>/dev/null", "aaPanel"),
]

for cmd, desc in tests:
    out, _, _ = run(client, cmd, timeout=15)
    print(f"  {desc}: {out if out else 'N/A'}")

client.close()
print("\n" + "=" * 60)
