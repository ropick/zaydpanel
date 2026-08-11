import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()

# Use Prisma + bcryptjs directly
js_script = '''const bcrypt = require('bcryptjs');
const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();

async function main() {
  const hash = bcrypt.hashSync('Admin123', 12);
  console.log('Generated hash:', hash.substring(0, 15) + '...');
  console.log('Hash length:', hash.length);

  const result = await p.user.update({
    where: { email: 'admin@zaydcluster.com' },
    data: { password: hash }
  });
  console.log('Updated user:', result.email);

  // Verify
  const verify = bcrypt.compareSync('Admin123', hash);
  console.log('Verify Admin123:', verify);

  await p.$disconnect();
  console.log('DONE');
}

main().catch(e => { console.error(e); process.exit(1); });
'''

with sftp.file('/tmp/update_pw_final.js', 'w') as f:
    f.write(js_script)

with sftp.file('/tmp/apply_final.sh', 'w') as f:
    f.write('''#!/bin/bash
docker cp /tmp/update_pw_final.js zaydcluster-app:/app/update_pw.js
echo '=== RUN ==='
docker exec -w /app zaydcluster-app node update_pw.js
echo ''
echo '=== RESTART ==='
docker restart zaydcluster-app
sleep 8
echo '=== STATUS ==='
docker ps --format 'table {{.Names}}\\t{{.Status}}'
echo ''
echo '=== TEST LOGIN API ==='
curl -s -X POST http://localhost:3000/api/auth/callback/credentials -H "Content-Type: application/x-www-form-urlencoded" -d "email=admin@zaydcluster.com&password=Admin123&callbackUrl=http://localhost:3000/admin" -o /dev/null -w "HTTP: %{http_code}" 2>&1
echo ''
echo '=== DONE ==='
''')
sftp.chmod('/tmp/apply_final.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('bash /tmp/apply_final.sh\n')

output = ''
for _ in range(50):
    time.sleep(0.5)
    try:
        while channel.recv_ready():
            data = channel.recv(4096)
            output += data.decode(errors='replace')
    except:
        pass

print(output)
ssh.close()
