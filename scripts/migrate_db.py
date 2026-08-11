import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Run prisma migrate and prisma db push
print("=== Running Prisma DB Push ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app npx prisma db push --accept-data-loss 2>&1',
    timeout=60
)
stdin.channel.settimeout(60)
out = stdout.read().decode().strip()
err = stderr.read().decode().strip()
print(out or err)

print("\n=== Verifying tables ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app npx prisma db execute --stdin --schema=/app/prisma/schema.prisma <<< "SELECT name FROM sqlite_master WHERE type=\'table\';" 2>&1',
    timeout=30
)
stdin.channel.settimeout(30)
print(stdout.read().decode().strip() or stderr.read().decode().strip())

ssh.close()
