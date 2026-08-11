import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()

# Use better-sqlite3 (prisma dep) + bcryptjs
js_script = '''const bcrypt = require('bcryptjs');
const Database = require('/app/node_modules/better-sqlite3');
const db = new Database('/app/db/custom.db');

const hash = bcrypt.hashSync('Admin123', 12);
console.log('Generated hash:', hash.substring(0, 15) + '...');
console.log('Hash length:', hash.length);

const result = db.prepare("UPDATE User SET password = ? WHERE email = 'admin@zaydcluster.com'").run(hash);
console.log('Rows updated:', result.changes);

const row = db.prepare("SELECT password FROM User WHERE email = 'admin@zaydcluster.com'").get();
console.log('Stored hash length:', row.password.length);
console.log('Starts with $2a$:', row.password.startsWith('$2a$'));

const verify = bcrypt.compareSync('Admin123', row.password);
console.log('Verify Admin123:', verify);

db.close();
console.log('DONE');
'''

with sftp.file('/tmp/update_pw3.js', 'w') as f:
    f.write(js_script)

with sftp.file('/tmp/apply_js3.sh', 'w') as f:
    f.write('''#!/bin/bash
docker cp /tmp/update_pw3.js zaydcluster-app:/app/update_pw.js
echo '=== RUN ==='
docker exec -w /app zaydcluster-app node update_pw.js
echo ''
echo '=== RESTART ==='
docker restart zaydcluster-app
sleep 8
echo '=== STATUS ==='
docker ps --format 'table {{.Names}}\\t{{.Status}}'
echo ''
echo '=== DONE ==='
''')
sftp.chmod('/tmp/apply_js3.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('bash /tmp/apply_js3.sh\n')

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
