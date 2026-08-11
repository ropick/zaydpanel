import paramiko
import time

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Recreate container properly - stop, remove, then up (which reads .env)
print("=== Recreating container with proper env ===")
cmd = 'cd /opt/zaydcluster/deploy && sudo docker compose stop app && sudo docker compose rm -f app'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
stdin.channel.settimeout(30)
print(stdout.read().decode().strip())

# Create + start with docker compose up (reads env_file: ../.env)
cmd2 = 'cd /opt/zaydcluster/deploy && sudo docker compose up -d app'
stdin, stdout, stderr = ssh.exec_command(cmd2, timeout=30)
stdin.channel.settimeout(30)
print(stdout.read().decode().strip())

time.sleep(5)

# Verify env vars now
print("\n=== Verify env vars ===")
env_checks = [
    'GMAIL_USER', 'PROVISION_SECRET', 'XENDIT_WEBHOOK_TOKEN', 'NEXTAUTH_URL', 'NEXTAUTH_SECRET'
]
for var in env_checks:
    stdin, stdout, stderr = ssh.exec_command(
        f'sudo docker exec zaydcluster-app sh -c "echo {var}=${{{var}:-NOT_SET}}"',
        timeout=10
    )
    stdin.channel.settimeout(10)
    val = stdout.read().decode().strip()
    mark = "✅" if 'NOT_SET' not in val else "❌"
    print(f"  {mark} {var}: {val[:60]}")

# Quick API test
print("\n=== Quick API test ===")
stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" http://localhost:3000', timeout=10)
stdin.channel.settimeout(10)
print(f"  App HTTP: {stdout.read().decode().strip()}")

stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:3000/api/auth/csrf 2>&1 | head -c 80', timeout=10)
stdin.channel.settimeout(10)
print(f"  CSRF: {stdout.read().decode().strip()}")

# Test provision from container
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app wget -qO- --timeout=5 http://host.docker.internal:9999/health 2>&1',
    timeout=15
)
stdin.channel.settimeout(15)
print(f"  Provision API: {stdout.read().decode().strip()}")

ssh.close()
