import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/reset_pw_final.sh', 'w') as f:
    # Use python3 inside the script to handle the hash safely
    f.write('''#!/bin/bash
docker cp zaydcluster-app:/app/db/custom.db /tmp/pw_fix.db

python3 << 'PYEOF'
import sqlite3, bcrypt

db_path = '/tmp/pw_fix.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Generate new bcrypt hash
new_hash = bcrypt.hashpw(b'Admin123', bcrypt.gensalt(12)).decode()
print(f"New hash: {new_hash}")
print(f"Hash length: {len(new_hash)}")

# Update the password
cursor.execute("UPDATE User SET password = ? WHERE email = 'admin@zaydcluster.com'", (new_hash,))
conn.commit()

# Verify
cursor.execute("SELECT password FROM User WHERE email = 'admin@zaydcluster.com'")
stored = cursor.fetchone()[0]
print(f"Stored: {stored[:20]}...")
print(f"Stored length: {len(stored)}")
verify = bcrypt.checkpw(b'Admin123', stored.encode())
print(f"Verify result: {verify}")
conn.close()
PYEOF

echo ''
echo '=== COPY TO CONTAINER ==='
docker cp /tmp/pw_fix.db zaydcluster-app:/app/db/custom.db
echo 'Done'

echo ''
echo '=== RESTART ==='
docker restart zaydcluster-app
sleep 8

echo ''
echo '=== STATUS ==='
docker ps --format 'table {{.Names}}\t{{.Status}}'
echo ''
echo '=== ALL DONE ==='
''')
sftp.chmod('/tmp/reset_pw_final.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('bash /tmp/reset_pw_final.sh\n')

output = ''
for _ in range(40):
    time.sleep(0.5)
    try:
        while channel.recv_ready():
            data = channel.recv(4096)
            output += data.decode(errors='replace')
    except:
        pass

print(output)
ssh.close()
