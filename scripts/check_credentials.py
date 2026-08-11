import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=10)

# Use sftp to avoid shell quoting issues with parentheses
sftp = ssh.open_sftp()

files = [
    '/opt/zaydcluster/src/app/(client)/dashboard/page.tsx',
    '/opt/zaydcluster/src/app/(client)/profile/page.tsx',
]

for f in files:
    print(f"\n{'='*60}")
    print(f"FILE: {f}")
    print(f"{'='*60}")
    try:
        with sftp.open(f, 'r') as fh:
            content = fh.read().decode()
            print(content[:8000])
    except Exception as e:
        print(f"ERROR: {e}")

sftp.close()
ssh.close()
