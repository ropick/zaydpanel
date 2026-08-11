import paramiko
import time

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Fix nginx port conflict and verify everything running
cmds = [
    ('sudo docker ps -a --format "{{.Names}} {{.Status}} {{.Ports}}" 2>&1', 15),
    ('sudo ss -tlnp | grep -E ":80|:443|:3000" 2>&1', 15),
]

for cmd, t in cmds:
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=t)
    stdin.channel.settimeout(t)
    print(stdout.read().decode().strip())

# Restart nginx container
print("\n=== Restart nginx ===")
stdin, stdout, stderr = ssh.exec_command('cd /opt/zaydcluster/deploy && sudo docker compose up -d nginx 2>&1', timeout=30)
stdin.channel.settimeout(30)
print(stdout.read().decode().strip())

time.sleep(3)

# Check if app is accessible
print("\n=== Test app directly from host ===")
stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>&1', timeout=15)
stdin.channel.settimeout(15)
print(f"App HTTP status: {stdout.read().decode().strip()}")

stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" https://staging.pro99.my.id 2>&1 || curl -s -o /dev/null -w "%{http_code}" http://localhost:80 2>&1', timeout=15)
stdin.channel.settimeout(15)
print(f"Nginx HTTP status: {stdout.read().decode().strip()}")

ssh.close()
