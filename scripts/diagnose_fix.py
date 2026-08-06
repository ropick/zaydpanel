import paramiko, time, sys

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

print("=== DIAGNOSA VPS 168.110.210.148 ===\n")

client = connect()

# 1. Check Docker service
print("[1] Docker service status:")
out, err, code = run(client, "sudo systemctl is-active docker")
print(f"    Docker: {out if out else err}")

# 2. Check all containers
print("\n[2] All Docker containers:")
out, err, code = run(client, "sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
print(out if out else "No containers found")

# 3. Check if compose file exists
print("\n[3] Compose file check:")
out, err, code = run(client, "ls -la /opt/nusahost/deploy/docker-compose.yml 2>&1")
print(f"    {out}")

# 4. Check Docker compose version
print("\n[4] Docker compose check:")
out, err, code = run(client, "sudo docker compose version 2>&1 || sudo docker-compose version 2>&1")
print(f"    {out}")

# 5. Check ports listening
print("\n[5] Ports listening:")
out, err, code = run(client, "sudo ss -tlnp | grep -E ':(80|443|3000|8090|8888) '")
print(f"    {out if out else 'No relevant ports listening'}")

# 6. Check nginx config
print("\n[6] Nginx config:")
out, err, code = run(client, "ls -la /opt/nusahost/deploy/nginx.conf 2>&1")
print(f"    {out}")

# 7. Check if aaPanel or any panel is installed
print("\n[7] Control panel check:")
out, err, code = run(client, "which bt 2>/dev/null && echo 'aaPanel found' || echo 'aaPanel not found'")
print(f"    {out}")
out, err, code = run(client, "which cyberpanel 2>/dev/null && echo 'CyberPanel found' || echo 'CyberPanel not found'")
print(f"    {out}")

# 8. Check disk space
print("\n[8] Disk space:")
out, err, code = run(client, "df -h / | tail -1")
print(f"    {out}")

# 9. Check memory
print("\n[9] Memory:")
out, err, code = run(client, "free -h | head -2")
print(f"    {out}")

print("\n=== PERBAIKAN ===\n")

# Fix: restart containers
print("[FIX] Restarting Docker containers...")
out, err, code = run(client, "cd /opt/nusahost/deploy && sudo docker compose down 2>&1", timeout=60)
print(f"    docker compose down: exit={code}")
if err:
    print(f"    stderr: {err}")

time.sleep(3)

out, err, code = run(client, "cd /opt/nusahost/deploy && sudo docker compose up -d 2>&1", timeout=120)
print(f"    docker compose up -d: exit={code}")
if out:
    print(f"    stdout: {out}")
if err:
    print(f"    stderr: {err}")

time.sleep(5)

# Verify
print("\n=== VERIFIKASI ===\n")
out, err, code = run(client, "sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'")
print(out if out else "No containers running")

out, err, code = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:80 2>/dev/null")
print(f"\nPort 80 (Nginx): HTTP {out}")

out, err, code = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000 2>/dev/null")
print(f"Port 3000 (App): HTTP {out}")

out, err, code = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:443 2>/dev/null")
print(f"Port 443 (SSL): HTTP {out}")

# Check logs if still failing
out, err, code = run(client, "sudo docker logs nusahost-nginx --tail 20 2>&1")
print(f"\nNginx logs (last 20):\n{out}")

out, err, code = run(client, "sudo docker logs nusahost-app --tail 20 2>&1")
print(f"\nApp logs (last 20):\n{out}")

client.close()
print("\n=== SELESAI ===")
