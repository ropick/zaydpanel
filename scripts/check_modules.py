import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/apply_js4.sh', 'w') as f:
    f.write('''#!/bin/bash
echo '=== CHECK WHAT SQLITE MODULES EXIST ==='
docker exec zaydcluster-app ls /app/node_modules/ 2>/dev/null | head -20
echo ''
docker exec zaydcluster-app find /app/node_modules -name '*sqlite*' -type d 2>/dev/null
echo ''
docker exec zaydcluster-app find /app/node_modules -name '*sqlite*' -type f 2>/dev/null | head -10
echo ''
echo '=== CHECK PRISMA CLIENT ==='
docker exec zaydcluster-app ls /app/node_modules/@prisma/ 2>/dev/null
echo ''
echo '=== TRY PRISMA APPROACH ==='
docker exec -w /app zaydcluster-app node -e "
const { PrismaClient } = require('@prisma/client');
const p = new PrismaClient();
const hash = '$2a$12$FAKE_HASH_FOR_TEST';
p.user.update({where:{email:'admin@zaydcluster.com'}, data:{password:hash}}).then(r => {
  console.log('Prisma update works!');
  p.\\$disconnect();
}).catch(e => console.error('Error:', e.message));
" 2>&1
''')
sftp.chmod('/tmp/apply_js4.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('bash /tmp/apply_js4.sh\n')

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
