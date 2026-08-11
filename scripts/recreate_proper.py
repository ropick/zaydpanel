import paramiko
import time

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Check what image the running container uses
print("=== Current container image ===")
cmd = 'sudo docker inspect zaydcluster-app --format "{{.Config.Image}} | Created: {{.Created}}" 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
print(f"  {stdout.read().decode().strip()}")

# Check latest built image
cmd = 'sudo docker images deploy-app --format "{{.ID}} | Created: {{.CreatedAt}} | Size: {{.Size}}" 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
print(f"\nLatest image: {stdout.read().decode().strip()}")

# Force recreate: stop, rm, then create fresh
print("\n=== Force recreate container ===")
cmds = [
    'cd /opt/zaydcluster/deploy && sudo docker compose stop app 2>&1',
    'cd /opt/zaydcluster/deploy && sudo docker compose rm -f app 2>&1',
    'sudo docker rm zaydcluster-app 2>/dev/null; echo "cleaned"',
    'cd /opt/zaydcluster/deploy && sudo docker compose create app 2>&1',
    'cd /opt/zaydcluster/deploy && sudo docker compose start app 2>&1',
]
for cmd in cmds:
    print(f"  {cmd[:70]}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    stdin.channel.settimeout(30)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"  => {out or err}")

time.sleep(5)

# NOW verify env vars
print("\n=== Verify env vars after recreate ===")
env_checks = [
    'GMAIL_USER', 'PROVISION_SECRET', 'XENDIT_WEBHOOK_TOKEN', 'NEXTAUTH_URL'
]
for var in env_checks:
    stdin, stdout, stderr = ssh.exec_command(
        f'sudo docker exec zaydcluster-app sh -c "echo {var}=${{{var}:-NOT_SET}}"',
        timeout=10
    )
    stdin.channel.settimeout(10)
    val = stdout.read().decode().strip()
    mark = "✅" if 'NOT_SET' not in val else "❌"
    print(f"  {mark} {val[:80]}")

# Also test compiled code
print("\n=== Verify compiled code ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app grep -c "cpPassword" /app/.next/server/chunks/_0ltpzvg._.js 2>/dev/null || echo "0"',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"  cpPassword count: {stdout.read().decode().strip()}")

stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app grep -c "host.docker.internal" /app/.next/server/chunks/_0ltpzvg._.js 2>/dev/null || echo "0"',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"  host.docker.internal count: {stdout.read().decode().strip()}")

stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app grep -c "Login Credentials" /app/.next/server/chunks/_0ltpzvg._.js 2>/dev/null || echo "0"',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"  Login Credentials count: {stdout.read().decode().strip()}")

# Test app health
stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" http://localhost:3000', timeout=10)
stdin.channel.settimeout(10)
print(f"\n  App HTTP: {stdout.read().decode().strip()}")

stdin, stdout, stderr = ssh.exec_command('sudo docker ps --filter name=zaydcluster-app --format "{{.Names}} {{.Status}}"', timeout=10)
stdin.channel.settimeout(10)
print(f"  Container: {stdout.read().decode().strip()}")

ssh.close()
