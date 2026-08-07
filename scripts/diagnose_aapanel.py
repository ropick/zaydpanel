#!/usr/bin/env python3
"""Diagnose aaPanel connection reset on port 36977"""
import paramiko

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
print("DIAGNOSE: aaPanel Connection Reset on Port 36977")
print("=" * 60)

# 1. Check if aaPanel process is running
print("\n[1] aaPanel process status...")
out, err, code = run(client, "ps aux | grep -E '(BT-Panel|aapanel|python.*panel)' | grep -v grep")
print(f"  Process: {out if out else 'NOT RUNNING'}")

# 2. Check what's listening on port 36977 (host level)
print("\n[2] Port 36977 listeners (host)...")
out, err, code = run(client, "sudo ss -tlnp | grep 36977")
print(f"  Listeners: {out if out else 'NONE - nothing listening on 36977!'}")

# 3. Check aaPanel status
print("\n[3] aaPanel CLI status...")
out, err, code = run(client, "sudo bt status 2>&1")
print(f"  Status: {out if out else 'N/A'}")

# 4. Check Docker nginx logs for 36977 errors
print("\n[4] Docker nginx logs (last 20 lines)...")
out, err, code = run(client, "sudo docker logs nusahost-nginx --tail 20 2>&1")
print(f"  Logs: {out[:500] if out else 'N/A'}")

# 5. Check Docker nginx port mapping
print("\n[5] Docker container port mappings...")
out, err, code = run(client, "sudo docker ps --format '{{.Names}}: {{.Ports}}'")
print(f"  Ports: {out}")

# 6. Check Docker nginx config for 36977
print("\n[6] Docker nginx config (36977 section)...")
out, err, code = run(client, "sudo docker exec nusahost-nginx cat /etc/nginx/conf.d/default.conf 2>&1")
if "36977" in out:
    # Extract the 36977 block
    lines = out.split('\n')
    capture = False
    block = []
    for line in lines:
        if '36977' in line:
            capture = True
        if capture:
            block.append(line)
    print(f"  Config block: {'  '.join(block)}")
else:
    print(f"  No 36977 in Docker nginx config")
print(f"  Full config:\n{out}")

# 7. Try curl to localhost:36977 from host
print("\n[7] Curl test to localhost:36977 (from host)...")
out, err, code = run(client, "curl -sI http://localhost:36977 --connect-timeout 5 2>&1")
print(f"  Response: {out[:300] if out else 'TIMEOUT/FAILED'}")
print(f"  Error: {err[:200] if err else 'none'}")
print(f"  Exit code: {code}")

# 8. Try curl to aaPanel directly (bypass Docker nginx)
print("\n[8] Curl test to 127.0.0.1:36977 (direct, bypass Docker)...")
out, err, code = run(client, "curl -sI http://127.0.0.1:36977 --connect-timeout 5 2>&1")
print(f"  Response: {out[:300] if out else 'TIMEOUT/FAILED'}")
print(f"  Error: {err[:200] if err else 'none'}")
print(f"  Exit code: {code}")

# 9. Check aaPanel config for port and bind address
print("\n[9] aaPanel port configuration...")
out, err, code = run(client, "sudo cat /www/server/panel/data/port.pl 2>&1")
print(f"  Port file: {out if out else 'NOT FOUND'}")
out2, err2, code2 = run(client, "sudo cat /www/server/panel/data/bind_domain.conf 2>&1")
print(f"  Bind domain: {out2 if out2 else 'NOT FOUND'}")

# 10. Check if aaPanel python is running and its config
print("\n[10] aaPanel main config...")
out, err, code = run(client, "sudo cat /www/server/panel/config/config.json 2>&1")
print(f"  Config: {out[:500] if out else 'NOT FOUND'}")

# 11. Check systemd service
print("\n[11] bt systemd service...")
out, err, code = run(client, "sudo systemctl status bt 2>&1 | head -20")
print(f"  Service: {out[:400] if out else 'N/A'}")

client.close()
print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
