import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/rebuild.sh', 'w') as f:
    f.write('''#!/bin/bash
cd /opt/zaydcluster/deploy
echo '=== BUILDING NEW IMAGE ==='
docker compose build --no-cache app 2>&1 | tail -20
echo ''
echo '=== RESTARTING CONTAINER ==='
docker compose up -d app 2>&1
echo ''
echo '=== WAITING FOR STARTUP ==='
sleep 10
echo ''
echo '=== CONTAINER STATUS ==='
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
echo ''
echo '=== CHECK LOGS ==='
docker logs zaydcluster-app --tail 20 2>&1
echo ''
echo '=== DONE ==='
''')
sftp.chmod('/tmp/rebuild.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('bash /tmp/rebuild.sh\n')

output = ''
for _ in range(120):  # Up to 60 seconds for build
    time.sleep(0.5)
    try:
        while channel.recv_ready():
            data = channel.recv(4096)
            output += data.decode(errors='replace')
    except:
        pass

print(output)
ssh.close()
