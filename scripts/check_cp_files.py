import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_cp_files.sh', 'w') as f:
    f.write('''#!/bin/bash
echo '=== LOGO FILES ==='
find /usr/local/CyberCP -name 'logo*' -o -name 'favicon*' -o -name 'cyberpanel*.svg' -o -name 'cyberpanel*.png' 2>/dev/null
echo ''
echo '=== STATIC IMAGES ==='
ls /usr/local/CyberCP/static/CyberCP/images/ 2>/dev/null
echo ''
echo '=== LOGIN TEMPLATE ==='
find /usr/local/CyberCP -name '*login*' -name '*.html' 2>/dev/null
echo ''
echo '=== BASE TEMPLATE ==='
find /usr/local/CyberCP -name 'base.html' -o -name 'index.html' 2>/dev/null | head -20
echo ''
echo '=== TEMPLATE DIR ==='
find /usr/local/CyberCP -path '*/templates/*.html' 2>/dev/null | head -30
echo ''
echo '=== GREP cyberpanel IN HTML ==='
grep -rl 'CyberPanel' /usr/local/CyberCP/baseTemplate/ 2>/dev/null | head -20
grep -rl 'CyberPanel' /usr/local/CyberCP/ --include='*.html' 2>/dev/null | head -20
echo ''
echo '=== CHECK baseTemplate ==='
ls /usr/local/CyberCP/baseTemplate/ 2>/dev/null
echo ''
echo '=== STATIC CSS ==='
find /usr/local/CyberCP/static -name '*.css' 2>/dev/null | head -10
''')
sftp.chmod('/tmp/check_cp_files.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('bash /tmp/check_cp_files.sh\n')

output = ''
for _ in range(20):
    time.sleep(0.5)
    try:
        while channel.recv_ready():
            data = channel.recv(4096)
            output += data.decode(errors='replace')
    except: pass

print(output)
ssh.close()
