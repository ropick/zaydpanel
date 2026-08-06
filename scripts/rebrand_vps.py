import paramiko, os, time

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('168.110.210.148', username='opc', pkey=key, timeout=10)

print('Uploading updated files...')
sftp = c.open_sftp()
sftp.put('/home/z/my-project/src/app/page.tsx', '/opt/nusahost/src/app/page.tsx')
print('  page.tsx ✓')
sftp.put('/home/z/my-project/src/app/layout.tsx', '/opt/nusahost/src/app/layout.tsx')
print('  layout.tsx ✓')
sftp.put('/home/z/my-project/deploy/Dockerfile', '/opt/nusahost/deploy/Dockerfile')
print('  Dockerfile ✓')
sftp.close()

# Write rebuild script via SFTP
script = """#!/bin/bash
cd /opt/nusahost
echo "[$(date)] REBUILD" > /tmp/nusahost.log
sudo docker compose -f deploy/docker-compose.yml build --no-cache >> /tmp/nusahost.log 2>&1
echo "[$(date)] BUILD: $?" >> /tmp/nusahost.log
sudo docker compose -f deploy/docker-compose.yml up -d >> /tmp/nusahost.log 2>&1
echo "[$(date)] UP: $?" >> /tmp/nusahost.log
echo "[$(date)] DONE" >> /tmp/nusahost.log
"""
with c.open_sftp().file('/opt/nusahost/rebuild.sh', 'w') as f:
    f.write(script)
c.exec_command('chmod +x /opt/nusahost/rebuild.sh')

# Run in background
c.exec_command('nohup bash /opt/nusahost/rebuild.sh &>/dev/null &')

time.sleep(3)
o = c.exec_command('tail -5 /tmp/nusahost.log', timeout=10)[1].read().decode()
print(f'\nBuild started: {o}')
print('Rebuild running (~3-5 min). Brand changed to pro99.my.id')
c.close()
