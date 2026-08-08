import paramiko

key_path = '/home/z/my-project/deploy/nusahost_id'
host = '168.110.210.148'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file(key_path, password=None)
client.connect(host, username='opc', pkey=key, timeout=15)

def run_sudo(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(f"sudo bash -c '{cmd}'", timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err

# Find what's still using port 36977
print("=== What's on port 36977 ===")
out, err = run_sudo("ss -tlnp | grep 36977 && sudo lsof -i :36977 2>/dev/null || fuser 36977/tcp 2>/dev/null")
print(f"OUT: {out}")
if err: print(f"ERR: {err}")

# Check /www/server
print("\n=== /www/server contents ===")
out, err = run_sudo("ls -laR /www/server/ 2>/dev/null | head -50")
print(out)

# Kill anything remaining on 36977
print("\n=== Force kill remaining ===")
out, err = run_sudo("fuser -k 36977/tcp 2>/dev/null; sleep 2; ss -tlnp | grep 36977 || echo 'Port 36977 now FREE'")
print(out)

# Remove all remaining panel files
print("\n=== Full removal ===")
out, err = run_sudo("rm -rf /www/server 2>/dev/null && echo 'REMOVED /www/server' || echo 'FAILED to remove'")
print(out)
if err: print(f"ERR: {err}")

# Verify
out, err = run_sudo("ls /www/ 2>/dev/null && echo '---' && ss -tlnp | grep 36977 || echo 'ALL CLEAN'")
print(out)

client.close()
