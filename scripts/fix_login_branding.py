import paramiko, sys, time

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()
with sftp.file('/tmp/fix_login.sh', 'w') as f:
    f.write('''#!/bin/bash
set -e
echo '=== RESTORE BACKUP ==='
cp /tmp/login.html.bak /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html
echo 'Restored'

echo ''
echo '=== APPLY CHANGES CAREFULLY ==='
FILE=/usr/local/CyberCP/loginSystem/templates/loginSystem/login.html

# Title
sed -i 's|<title> Login - CyberPanel </title>|<title>Login - ZaydCluster</title>|' "$FILE"

# Meta description
sed -i 's|Login to your CyberPanel Account|Login to your ZaydCluster Account|' "$FILE"

# CyberPanel brand text (case sensitive, only in main headings)
sed -i 's|>CyberPanel<|>ZaydCluster<|g' "$FILE"
sed -i 's|> CyberPanel$|> ZaydCluster|g' "$FILE"

# Banner image
sed -i 's|/static/images/cyberpanel-banner-graphics.png|/static/images/zaydcluster-banner.svg|g' "$FILE"

# Heading text
sed -i 's|WEB HOSTING CONTROL PANEL|HOSTING MANAGEMENT|g' "$FILE"
sed -i 's|FOR EVERYONE|by ZaydCluster|g' "$FILE"

# Powered by text
sed -i 's|Powered By OpenLiteSpeed/LiteSpeed Enterprise. Built For Speed, Security and|Powered by OpenLiteSpeed. Speed, Security and|g' "$FILE"

echo 'Changes applied'

echo ''
echo '=== VERIFY ==='
echo 'Title:'
grep '<title>' "$FILE"
echo 'Brand:'
grep 'ZaydCluster' "$FILE" | head -5
echo 'Banner:'
grep 'zaydcluster-banner' "$FILE"
echo ''
echo '=== COPY TO PUBLIC ==='
cp "$FILE" /usr/local/CyberCP/public/loginSystem/templates/loginSystem/login.html 2>/dev/null || true
echo 'Done'
''')
sftp.chmod('/tmp/fix_login.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('sudo bash /tmp/fix_login.sh\n')

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
