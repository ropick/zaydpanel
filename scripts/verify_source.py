import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

sftp = ssh.open_sftp()

# Verify source file has the correct updated code
with sftp.open('/opt/zaydcluster/src/app/api/payment/callback/route.ts', 'r') as f:
    content = f.read().decode()

# Check for key strings
checks = [
    'creds.username',
    'creds.password',
    'hostingReadyEmail(',
    'host.docker.internal:9999',
    'cpUsername: creds.username',
    'cpPassword: creds.password',
]

print("=== Source file verification ===")
for c in checks:
    found = c in content
    print(f"  {'✅' if found else '❌'} {c}")

# Show the email sending part
idx = content.find('Send hosting ready email')
if idx >= 0:
    snippet = content[idx-100:idx+300]
    print(f"\n=== Email sending code snippet ===")
    print(snippet)

sftp.close()
ssh.close()
