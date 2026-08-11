import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

# Upload hash file
sftp = ssh.open_sftp()
sftp.put('/home/z/my-project/zaydcluster-admin-fix/hash.txt', '/tmp/bcrypt_hash.txt')
sftp.close()

# Now use a script that reads the hash from file (no shell variable interpolation)
sftp = ssh.open_sftp()
with sftp.file('/tmp/apply_hash.sh', 'w') as f:
    # Use read -r to read the hash safely, then use python3 (via container) to update
    f.write('''#!/bin/bash
docker cp zaydcluster-app:/app/db/custom.db /tmp/apply.db

# Read hash into variable safely
HASH=$(cat /tmp/bcrypt_hash.txt | tr -d '\\n')
echo "Hash length: ${#HASH}"
echo "Hash start: ${HASH:0:15}"

# Use sqlite3 with hex encoding to avoid shell interpretation issues
# First convert hash to hex, then update
HEX_HASH=$(echo -n "$HASH" | xxd -p | tr -d '\\n')
echo "Hex length: ${#HEX_HASH}"

# Get the user id
USER_ID=$(sqlite3 /tmp/apply.db "SELECT id FROM User WHERE email='admin@zaydcluster.com';")
echo "User ID: $USER_ID"

# Update using hex encoding to safely store the bcrypt hash
sqlite3 /tmp/apply.db "UPDATE User SET password = X'$HEX_HASH' WHERE id = '$USER_ID';"
echo "Password updated"

# Verify by reading back
sqlite3 /tmp/apply.db "SELECT length(password), substr(password,1,10) FROM User WHERE email='admin@zaydcluster.com';"

echo ''
echo '=== COPY TO CONTAINER ==='
docker cp /tmp/apply.db zaydcluster-app:/app/db/custom.db

echo ''
echo '=== RESTART ==='
docker restart zaydcluster-app
sleep 8

echo ''
echo '=== STATUS ==='
docker ps --format 'table {{.Names}}\\t{{.Status}}'

echo ''
echo '=== DONE ==='
''')
sftp.chmod('/tmp/apply_hash.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('bash /tmp/apply_hash.sh\n')

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
