import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)
sftp = ssh.open_sftp()

page_path = '/opt/zaydcluster/src/app/page.tsx'
with sftp.open(page_path, 'r') as f:
    content = f.read().decode()

lines = content.split('\n')

# Find all logo-related blocks with exact content
for i, line in enumerate(lines):
    if 'Logo' in line or ('rounded-lg bg-emerald-500' in line and 'Server' in lines[min(i+1, len(lines)-1)]):
        start = max(0, i-1)
        end = min(len(lines), i+8)
        print(f"\n--- Lines {start+1} to {end} ---")
        for j in range(start, end):
            marker = ">>>" if j == i else "   "
            print(f"  {marker} [{j+1}] {lines[j]}")

sftp.close()
ssh.close()
