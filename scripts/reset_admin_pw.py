import paramiko, sys, subprocess, time

# Generate bcrypt hash
result = subprocess.run(
    ['python3', '-c', '''
import bcrypt
password = "Admin123"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()
print(hashed)
'''],
    capture_output=True, text=True, timeout=10
)
new_hash = result.stdout.strip()
print(f'Generated hash: {new_hash}')

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

# Escape single quotes for shell/sqlite
safe_hash = new_hash.replace("'", "'\\''")

sftp = ssh.open_sftp()
with sftp.file('/tmp/reset_pw.sh', 'w') as f:
    f.write(f"""#!/bin/bash
echo '=== UPDATE PASSWORD ==='
sqlite3 /tmp/pw_check.db "UPDATE User SET password='{safe_hash}' WHERE email='admin@zaydcluster.com';"
echo 'Password updated'
echo ''
echo '=== VERIFY NEW HASH ==='
sqlite3 /tmp/pw_check.db "SELECT password FROM User WHERE email='admin@zaydcluster.com';"
echo ''
echo '=== COPY BACK TO CONTAINER ==='
docker cp /tmp/pw_check.db zaydcluster-app:/app/db/custom.db
echo 'DB copied'
echo ''
echo '=== RESTART CONTAINER ==='
docker restart zaydcluster-app
sleep 8
echo ''
echo '=== FINAL CHECK ==='
docker ps --format 'table {{.Names}}\\t{{.Status}}'
echo ''
echo '=== DONE ==='
""")
sftp.chmod('/tmp/reset_pw.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('bash /tmp/reset_pw.sh\n')

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
