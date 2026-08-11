import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

sftp = ssh.open_sftp()

# Check .env for any admin-related vars
print("=== .env file ===")
with sftp.open('/opt/zaydcluster/.env', 'r') as f:
    print(f.read().decode())

# Check admin seed or setup in source code
print("\n=== Looking for admin seed/setup ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo grep -rl "admin" /opt/zaydcluster/prisma/ 2>/dev/null',
    timeout=15
)
stdin.channel.settimeout(15)
files = stdout.read().decode().strip()
print(f"Files with 'admin' in prisma/: {files}")

# Check prisma seed
stdin, stdout, stderr = ssh.exec_command(
    'sudo cat /opt/zaydcluster/prisma/seed.ts 2>/dev/null || sudo cat /opt/zaydcluster/prisma/seed.js 2>/dev/null || echo "No seed file"',
    timeout=15
)
stdin.channel.settimeout(15)
print(f"\nSeed file:\n{stdout.read().decode()[:2000]}")

# Check auth-options for admin role setup
stdin, stdout, stderr = ssh.exec_command(
    'sudo grep -rl "ADMIN_EMAIL\\|admin.*password\\|role.*admin" /opt/zaydcluster/src/ 2>/dev/null | head -10',
    timeout=15
)
stdin.channel.settimeout(15)
admin_files = stdout.read().decode().strip()
print(f"\nFiles with admin references:\n{admin_files}")

sftp.close()
ssh.close()
