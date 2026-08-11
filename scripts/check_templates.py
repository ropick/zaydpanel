import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_templates.sh', 'w') as f:
    f.write('''#!/bin/bash
echo '=== INDEX.HTML (main sidebar/dashboard template) ==='
head -100 /usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html 2>/dev/null
echo ''
echo '=== LOGIN.HTML ==='
cat /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html 2>/dev/null
echo ''
echo '=== COSMETIC SETTINGS ==='
cat /usr/local/CyberCP/baseTemplate/cosmetic/models.py 2>/dev/null
echo ''
echo '=== LOGO FILE INFO ==='
file /usr/local/CyberCP/baseTemplate/static/baseTemplate/assets/image-resources/logo.png 2>/dev/null
file /usr/local/CyberCP/public/static/baseTemplate/assets/image-resources/logo.png 2>/dev/null
ls -la /usr/local/CyberCP/public/static/baseTemplate/assets/image-resources/logo*.png 2>/dev/null
''')
sftp.chmod('/tmp/check_templates.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('bash /tmp/check_templates.sh\n')

output = ''
for _ in range(30):
    time.sleep(0.5)
    try:
        while channel.recv_ready():
            output += channel.recv(4096).decode(errors='replace')
    except: pass

print(output)
ssh.close()
