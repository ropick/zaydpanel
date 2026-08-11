import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

sftp = ssh.open_sftp()

# Find ALL logo usage across the project
print("=== Searching all logo references ===")
files_to_check = []
cmd = 'sudo find /opt/zaydcluster/src -name "*.tsx" -o -name "*.ts" | head -50'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
all_files = stdout.read().decode().strip().split('\n')

for f_path in all_files:
    try:
        with sftp.open(f_path.strip(), 'r') as fh:
            content = fh.read().decode()
        for i, line in enumerate(content.split('\n')):
            if any(k in line.lower() for k in ['logo', 'favicon', 'icon.url', 'icon.png']):
                short = f_path.strip().replace('/opt/zaydcluster/', '')
                print(f"  {short}:{i+1} -> {line.strip()[:150]}")
    except:
        pass

# Also check public/logo.svg content
print("\n=== Current logo.svg ===")
try:
    with sftp.open('/opt/zaydcluster/public/logo.svg', 'r') as f:
        content = f.read().decode()
    print(content[:500])
except Exception as e:
    print(f"  {e}")

# Check app icon / metadata icons in root layout
print("\n=== Root layout.tsx metadata ===")
with sftp.open('/opt/zaydcluster/src/app/layout.tsx', 'r') as f:
    content = f.read().decode()
# Show metadata section
in_meta = False
for line in content.split('\n'):
    if 'metadata' in line or in_meta:
        print(f"  {line}")
        in_meta = True
        if line.strip().startswith('}') and in_meta and 'metadata' not in line:
            break

# Check page.tsx (landing page) for logo
print("\n=== Landing page logo ===")
with sftp.open('/opt/zaydcluster/src/app/page.tsx', 'r') as f:
    content = f.read().decode()
for i, line in enumerate(content.split('\n')):
    if 'logo' in line.lower() or 'zaydcluster' in line.lower() or 'icon' in line.lower():
        start = max(0, i-2)
        end = min(len(content.split('\n')), i+5)
        for j in range(start, end):
            print(f"  [{j}] {content.split(chr(10))[j][:150]}")
        print("  ---")

sftp.close()
ssh.close()
