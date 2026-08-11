import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh.connect('168.110.210.148', username='opc', pkey=key)

print("=== Rebuilding Docker container (no-cache for public assets) ===")

# Since only public/ files changed, we don't need --no-cache (they are copied as-is in Docker)
# Just rebuild and restart
cmds = [
    'cd /opt/zaydcluster/deploy && docker compose down 2>&1',
    'cd /opt/zaydcluster/deploy && docker compose build --no-cache 2>&1',
    'cd /opt/zaydcluster/deploy && docker compose up -d 2>&1',
]

# Run build in background with nohup because it takes a few minutes
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/zaydcluster/deploy && nohup bash -c "docker compose down && docker compose build --no-cache && docker compose up -d" > /tmp/docker_rebuild.log 2>&1 &',
    get_pty=False
)
print("Build started in background. Waiting...")

# Poll for completion
for i in range(60):  # max 5 minutes
    time.sleep(5)
    stdin, stdout, stderr = ssh.exec_command('cat /tmp/docker_rebuild.log')
    log = stdout.read().decode()
    
    # Check if docker compose up is done
    stdin2, stdout2, stderr2 = ssh.exec_command('docker ps --filter name=zaydcluster-app --format "{{.Status}}"')
    status = stdout2.read().decode().strip()
    
    if status:
        print(f"\nContainer is running! Status: {status}")
        break
    
    # Show last few lines of build log
    lines = log.strip().split('\n')
    if lines:
        print(f"  [{i*5}s] {lines[-1][:100]}")

# Final check
stdin, stdout, stderr = ssh.exec_command('docker ps --filter name=zaydcluster-app --format "{{.Status}}"')
status = stdout.read().decode().strip()
print(f"\nFinal container status: {status}")

# Verify the new circular logo is served
stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{size_download}" http://localhost:3000/logo-64.png')
size = stdout.read().decode().strip()
print(f"Logo-64.png size from app: {size} bytes")

# Check favicon
stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{size_download}" http://localhost:3000/favicon-32.png')
size = stdout.read().decode().strip()
print(f"Favicon-32.png size from app: {size} bytes")

# Verify Nginx serves the new files
stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{size_download}" https://pro99.my.id/logo-64.png')
size = stdout.read().decode().strip()
print(f"Logo-64.png via Nginx: {size} bytes")

stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{size_download}" https://pro99.my.id/favicon-32.png')
size = stdout.read().decode().strip()
print(f"Favicon-32.png via Nginx: {size} bytes")

ssh.close()
print("\n=== Done ===")
