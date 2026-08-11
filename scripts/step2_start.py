import paramiko
import time

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

print("=== Starting container ===")
stdin, stdout, stderr = ssh.exec_command('cd /opt/zaydcluster/deploy && sudo docker compose up -d 2>&1', timeout=60)
stdin.channel.settimeout(60)
print(stdout.read().decode().strip())
err = stderr.read().decode().strip()
if err:
    print(f"ERR: {err}")

time.sleep(8)

print("\n=== Verifying compiled code has credentials ===")
checks = [
    'creds.username',
    'creds.password',
    'Login Panel Hosting',
    'cpPassword',
    'host.docker.internal',
]

for kw in checks:
    stdin, stdout, stderr = ssh.exec_command(
        f'sudo docker exec zaydcluster-app grep -rc "{kw}" /app/.next/server/chunks/_0ltpzvg._.js 2>/dev/null || echo "0"',
        timeout=15
    )
    stdin.channel.settimeout(15)
    count = stdout.read().decode().strip()
    print(f"  {kw}: {count} matches")

print("\n=== Container status ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker ps --filter name=zaydcluster-app --format "{{.Names}} {{.Status}}"',
    timeout=15
)
stdin.channel.settimeout(15)
print(stdout.read().decode().strip())

print("\n=== Container logs (last 5) ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker logs zaydcluster-app --tail 5 2>&1',
    timeout=15
)
stdin.channel.settimeout(15)
print(stdout.read().decode())

ssh.close()
print("\nDone!")
