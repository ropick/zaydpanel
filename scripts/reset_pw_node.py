import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()

# Write a Python script on the server that generates the hash and updates DB directly
# Use the container's node.js with bcryptjs since container has it
with sftp.file('/tmp/gen_hash.js', 'w') as f:
    f.write('''const bcrypt = require('bcryptjs');
const hash = bcrypt.hashSync('Admin123', 12);
console.log(hash);
''')

with sftp.file('/tmp/reset_pw_node.sh', 'w') as f:
    f.write('''#!/bin/bash
echo '=== GENERATE BCRYPT HASH VIA NODE ==='
HASH=$(docker exec zaydcluster-app node -e "const b=require('bcryptjs');console.log(b.hashSync('Admin123',12))")
echo "Hash: $HASH"
echo "Length: ${#HASH}"

echo ''
echo '=== COPY DB OUT ==='
docker cp zaydcluster-app:/app/db/custom.db /tmp/node_pw.db

echo ''
echo '=== UPDATE PASSWORD ==='
# Use node inside container to update the DB directly
docker exec zaydcluster-app node -e "
const bcrypt = require('bcryptjs');
const { DatabaseSync } = require('node:sqlite');
const db = new DatabaseSync('/app/db/custom.db');
const hash = bcrypt.hashSync('Admin123', 12);
db.prepare(\"UPDATE User SET password = ? WHERE email = 'admin@zaydcluster.com'\").run(hash);
const row = db.prepare(\"SELECT password FROM User WHERE email = 'admin@zaydcluster.com'\").get();
console.log('Stored hash length:', row.password.length);
console.log('Starts with $2a$:', row.password.startsWith('$2a$'));
const verify = bcrypt.compareSync('Admin123', row.password);
console.log('Verify Admin123:', verify);
db.close();
"

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
sftp.chmod('/tmp/reset_pw_node.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('bash /tmp/reset_pw_node.sh\n')

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
