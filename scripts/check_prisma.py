import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

sftp = ssh.open_sftp()

# Check package.json for prisma version
print("=== package.json prisma version ===")
with sftp.open('/opt/zaydcluster/package.json', 'r') as f:
    content = f.read().decode()
for line in content.split('\n'):
    if 'prisma' in line.lower():
        print(f"  {line}")

# Check schema.prisma
print("\n=== schema.prisma ===")
with sftp.open('/opt/zaydcluster/prisma/schema.prisma', 'r') as f:
    content = f.read().decode()
print(content[:3000])

sftp.close()
ssh.close()
