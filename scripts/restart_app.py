import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Only public folder changed (images), not source code that needs recompile
# Just restart container to pick up new public files
print("=== Restarting container (public files changed) ===")
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/zaydcluster/deploy && sudo docker compose restart app 2>&1',
    timeout=30
)
stdin.channel.settimeout(30)
print(stdout.read().decode().strip())
err = stderr.read().decode().strip()
if err:
    print(f"ERR: {err}")

import time
time.sleep(5)

# Verify new files are in container
print("\n=== Verify files in container ===")
for f in ['logo-64.png', 'logo-256.png', 'favicon-32.png', 'favicon-16.png', 'apple-touch-icon.png']:
    stdin, stdout, stderr = ssh.exec_command(
        f'sudo docker exec zaydcluster-app ls -la /app/public/{f} 2>&1',
        timeout=10
    )
    stdin.channel.settimeout(10)
    print(f"  {stdout.read().decode().strip() or 'NOT FOUND'}")

# Verify app running
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker ps --filter name=zaydcluster-app --format "{{.Names}} {{.Status}}"',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"\nContainer: {stdout.read().decode().strip()}")

stdin, stdout, stderr = ssh.exec_command(
    'curl -s -o /dev/null -w "%{http_code}" http://localhost:3000',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"App HTTP: {stdout.read().decode().strip()}")

# Verify favicon accessible
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/favicon-32.png',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"Favicon: {stdout.read().decode().strip()}")

stdin, stdout, stderr = ssh.exec_command(
    'curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/logo-64.png',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"Logo 64: {stdout.read().decode().strip()}")

ssh.close()
