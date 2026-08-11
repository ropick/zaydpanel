import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/verify_pw.sh', 'w') as f:
    f.write('''#!/bin/bash
docker cp zaydcluster-app:/app/db/custom.db /tmp/verify.db
HASH=$(sqlite3 /tmp/verify.db "SELECT password FROM User WHERE email='admin@zaydcluster.com';")
echo "HASH_LENGTH: ${#HASH}"
echo "HASH_START: ${HASH:0:10}"
python3 << 'PYEOF'
import subprocess, bcrypt
result = subprocess.run(['sqlite3', '/tmp/verify.db', "SELECT password FROM User WHERE email='admin@zaydcluster.com';"], capture_output=True, text=True)
stored = result.stdout.strip()
print(f"Stored hash: {stored[:20]}...")
print(f"Length: {len(stored)}")
print(f"Starts with $2b$: {stored.startswith('$2b$')}")
verify = bcrypt.checkpw(b'Admin123', stored.encode())
print(f"Verify Admin123: {verify}")
PYEOF
echo '=== DONE ==='
''')
sftp.chmod('/tmp/verify_pw.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('bash /tmp/verify_pw.sh\n')

output = ''
for _ in range(20):
    time.sleep(0.5)
    try:
        while channel.recv_ready():
            data = channel.recv(4096)
            output += data.decode(errors='replace')
    except:
        pass

print(output)
ssh.close()
