import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Install prisma@6 and run db push
print("=== Install prisma@6 in container ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app sh -c "cd /app && npm install prisma@6 --no-save --legacy-peer-deps 2>&1 | tail -5"',
    timeout=120
)
stdin.channel.settimeout(120)
out = stdout.read().decode().strip()
err = stderr.read().decode().strip()
print(out or err)

# Now run db push with correct version
print("\n=== Running prisma db push (v6) ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app sh -c "cd /app && npx prisma db push --accept-data-loss 2>&1"',
    timeout=60
)
stdin.channel.settimeout(60)
out = stdout.read().decode().strip()
err = stderr.read().decode().strip()
print(out or err)

ssh.close()
