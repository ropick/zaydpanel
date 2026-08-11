import paramiko
import time

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Build and recreate container (only public folder changed, deps cached)
print("=== Rebuilding container (public files updated) ===")
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/zaydcluster/deploy && sudo docker compose up -d --build app 2>&1',
    timeout=300
)
stdin.channel.settimeout(300)
out = stdout.read().decode()
err = stderr.read().decode()
output = out + err
lines = output.strip().split('\n')
# Print last 15 lines
for line in lines[-15:]:
    print(f"  {line}")

time.sleep(5)

# Verify
print("\n=== Verify files ===")
for f in ['logo-64.png', 'favicon-32.png', 'apple-touch-icon.png']:
    stdin, stdout, stderr = ssh.exec_command(
        f'sudo docker exec zaydcluster-app ls -la /app/public/{f} 2>&1',
        timeout=10
    )
    stdin.channel.settimeout(10)
    print(f"  {stdout.read().decode().strip() or 'NOT FOUND'}")

# Test HTTP
stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/logo-64.png', timeout=10)
stdin.channel.settimeout(10)
print(f"\nLogo 64 HTTP: {stdout.read().decode().strip()}")

stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/favicon-32.png', timeout=10)
stdin.channel.settimeout(10)
print(f"Favicon HTTP: {stdout.read().decode().strip()}")

stdin, stdout, stderr = ssh.exec_command('sudo docker ps --filter name=zaydcluster-app --format "{{.Names}} {{.Status}}"', timeout=10)
stdin.channel.settimeout(10)
print(f"Container: {stdout.read().decode().strip()}")

ssh.close()
