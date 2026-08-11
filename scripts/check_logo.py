import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

sftp = ssh.open_sftp()

# Check public directory for current logo/favicon
print("=== Current logo/favicon files ===")
for pattern in ['logo*', 'favicon*', 'icon*', '*.ico', '*.png']:
    cmd = f'sudo find /opt/zaydcluster/public -iname "{pattern}" -type f 2>/dev/null'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    stdin.channel.settimeout(10)
    out = stdout.read().decode().strip()
    if out:
        for line in out.split('\n'):
            print(f"  {line}")

# Check layout/metadata for favicon
print("\n=== Checking layout.tsx for logo/meta ===")
for f in ['/opt/zaydcluster/src/app/layout.tsx', '/opt/zaydcluster/src/app/(client)/layout.tsx', '/opt/zaydcluster/src/app/(auth)/login/page.tsx']:
    try:
        with sftp.open(f, 'r') as fh:
            content = fh.read().decode()
        # Find logo-related code
        for i, line in enumerate(content.split('\n')):
            if any(k in line.lower() for k in ['logo', 'favicon', 'icon', 'image/png']):
                start = max(0, i-1)
                end = min(len(content.split('\n')), i+4)
                for j in range(start, end):
                    print(f"  [{f.split('/')[-1]}:{j}] {content.split(chr(10))[j][:150]}")
                print("  ---")
    except Exception as e:
        print(f"  {f}: {e}")

sftp.close()
ssh.close()
