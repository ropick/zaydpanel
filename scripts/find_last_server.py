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
for i, line in enumerate(lines):
    if 'Server className="w-5 h-5' in line:
        start = max(0, i-3)
        end = min(len(lines), i+5)
        for j in range(start, end):
            print(f"  [{j+1}] {lines[j]}")

sftp.close()
ssh.close()
