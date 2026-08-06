#!/usr/bin/env python3
"""FASE 3D-E: Install Nginx + configure reverse proxy on Oracle Linux (dnf)"""
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
print("FASE 3D-E: Install Nginx + Reverse Proxy (Oracle Linux)")
print("=" * 60)

client = connect()

# Check OS
out, _, _ = run(client, "cat /etc/os-release | head -3")
print(f"OS: {out}")

# === STEP 1: Install Nginx via dnf ===
print("\n[1] Installing Nginx (dnf)...")
out, err, code = run(client, "sudo dnf install -y nginx 2>&1 | tail -15", timeout=180)
print(f"  dnf install: code={code}")
if out:
    for line in out.split('\n')[-5:]:
        print(f"  {line}")

# Verify
out, _, _ = run(client, "which nginx 2>/dev/null && sudo nginx -v 2>&1")
print(f"  Nginx binary: {out}")

# === STEP 2: Create reverse proxy config ===
print("\n[2] Creating reverse proxy config...")

nginx_conf = """server {
    listen 80;
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

# Remove default config and add ours
cmds = [
    f"""cat > /tmp/staging.conf << 'NEOF'\n{nginx_conf}\nNEOF""",
    "sudo mkdir -p /www/wwwlogs",
    "sudo cp /tmp/staging.conf /etc/nginx/conf.d/staging.pro99.my.id.conf",
    "sudo rm -f /etc/nginx/conf.d/default.conf",
    # Also update main nginx.conf to not conflict
]

for cmd in cmds:
    out, err, code = run(client, cmd, timeout=15)
    if code != 0:
        print(f"  ⚠️ {cmd[:50]}: {err}")

# Test config
out, err, code = run(client, "sudo nginx -t 2>&1")
print(f"  nginx -t: {out}")

if code == 0:
    # Start/reload nginx
    out, err, code = run(client, "sudo systemctl enable nginx 2>&1 && sudo systemctl start nginx 2>&1", timeout=30)
    print(f"  systemctl start: code={code}, {out}")
    
    if code != 0:
        # Maybe already running
        run(client, "sudo systemctl restart nginx 2>&1", timeout=30)
        print("  Restarted nginx")
else:
    print(f"  ❌ Config test failed!")
    # Show what's wrong
    out, _, _ = run(client, "sudo nginx -T 2>&1 | tail -20")
    print(f"  {out}")

# === STEP 3: Ensure port 80 is open in firewall ===
print("\n[3] Firewall check...")
out, _, _ = run(client, "sudo firewall-cmd --list-ports 2>/dev/null")
print(f"  Open ports: {out}")

# Add port 80 if missing
if "80/tcp" not in out:
    run(client, "sudo firewall-cmd --permanent --add-port=80/tcp 2>&1 && sudo firewall-cmd --reload 2>&1")
    print("  Added port 80")

# === STEP 4: Verify ===
print("\n[4] Verification...")
time.sleep(2)

# Ports
out, _, _ = run(client, "ss -tlnp | grep -E ':(80|3000|36977) '")
print(f"  Ports:\n{out if out else '  None'}")

# Next.js app
out, _, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000 2>/dev/null")
print(f"  Next.js (3000): HTTP {out}")

# Via nginx proxy
out, _, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' -H 'Host: staging.pro99.my.id' http://localhost:80 2>/dev/null")
print(f"  Nginx proxy (80): HTTP {out}")

# Direct IP
out, _, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://168.110.210.148 2>/dev/null")
print(f"  External (IP:80): HTTP {out}")

# aaPanel
out, _, _ = run(client, "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://localhost:36977/613ccb60 2>/dev/null")
print(f"  aaPanel (36977): HTTP {out}")

# Docker
out, _, _ = run(client, "docker ps --format '{{.Names}} {{.Status}} {{.Ports}}'")
print(f"  Docker: {out if out else 'No containers'}")

# Nginx status
out, _, _ = run(client, "sudo systemctl status nginx --no-pager 2>&1 | head -5")
print(f"  Nginx: {out}")

# aaPanel status
out, _, _ = run(client, "sudo bt status 2>/dev/null")
print(f"  aaPanel: {out}")

client.close()

print("\n" + "=" * 60)
print("CONFIGURATION COMPLETE")
print("=" * 60)
