import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/rebuild_login.sh', 'w') as f:
    f.write('''#!/bin/bash
cd /opt/zaydcluster/deploy
docker compose build app 2>&1
echo 'BUILD_EXIT='$?
docker compose up -d app 2>&1
sleep 10
echo '=== STATUS ==='
docker ps --format 'table {{.Names}}\\t{{.Status}}'
echo ''
echo '=== LOGS ==='
docker logs zaydcluster-app --tail 5 2>&1
echo ''
echo '=== DONE ==='
''')
sftp.chmod('/tmp/rebuild_login.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('nohup bash /tmp/rebuild_login.sh > /tmp/rebuild_login.log 2>&1 &\necho STARTED\n')

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
