import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

# Check if build is still running or complete
sftp = ssh.open_sftp()
with sftp.file('/tmp/rebuild2.sh', 'w') as f:
    f.write('''#!/bin/bash
echo '=== DOCKER IMAGES ==='
docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}' | head -10
echo ''
echo '=== CONTAINER STATUS ==='
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' | head -10
echo ''
echo '=== BUILD AGAIN (this time capture output) ==='
cd /opt/zaydcluster/deploy
docker compose build app 2>&1
echo 'BUILD_EXIT_CODE='$?
echo ''
echo '=== DEPLOY ==='
docker compose up -d app 2>&1
echo ''
echo '=== WAIT ==='
sleep 10
echo ''
echo '=== FINAL STATUS ==='
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
echo ''
echo '=== RECENT LOGS ==='
docker logs zaydcluster-app --tail 15 2>&1
echo ''
echo '=== ALL DONE ==='
''')
sftp.chmod('/tmp/rebuild2.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('nohup bash /tmp/rebuild2.sh > /tmp/rebuild_output.log 2>&1 &\n')
time.sleep(1)
channel.send('echo BUILD_STARTED\n')

output = ''
for _ in range(10):
    time.sleep(1)
    try:
        while channel.recv_ready():
            data = channel.recv(4096)
            output += data.decode(errors='replace')
    except:
        pass

print('Build started in background')
print(output)
ssh.close()
