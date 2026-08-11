import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Approach: Run prisma db push from the HOST using the project's node_modules
# First check if node_modules exists on host
print("=== Check host node_modules ===")
stdin, stdout, stderr = ssh.exec_command(
    'ls /opt/zaydcluster/node_modules/prisma/build/index.js 2>/dev/null && echo "FOUND" || echo "NOT_FOUND"',
    timeout=10
)
stdin.channel.settimeout(10)
print(stdout.read().decode().strip())

# Check if we can use the builder stage
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" | grep deploy',
    timeout=10
)
stdin.channel.settimeout(10)
print("\nImages:", stdout.read().decode().strip())

# Alternative: install prisma CLI in container temporarily
print("\n=== Installing prisma CLI in container ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app sh -c "cd /app && npm install prisma@5 --no-save 2>&1 | tail -5"',
    timeout=120
)
stdin.channel.settimeout(120)
print(stdout.read().decode().strip() or stderr.read().decode().strip())

# Now run db push
print("\n=== Running prisma db push ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app sh -c "cd /app && npx prisma db push --accept-data-loss 2>&1"',
    timeout=60
)
stdin.channel.settimeout(60)
out = stdout.read().decode().strip()
err = stderr.read().decode().strip()
print(out or err)

ssh.close()
