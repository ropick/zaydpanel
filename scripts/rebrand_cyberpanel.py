import paramiko, sys, time, os

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()

# Upload logo files
base = '/home/z/my-project/zaydcluster-admin-fix'
logo_files = {
    f'{base}/zaydcluster-logo.svg': '/tmp/zaydcluster-logo.svg',
    f'{base}/zaydcluster-full-logo.svg': '/tmp/zaydcluster-full-logo.svg',
    f'{base}/zaydcluster-banner.svg': '/tmp/zaydcluster-banner.svg',
}
for local, remote in logo_files.items():
    sftp.put(local, remote)
    print(f'Uploaded: {os.path.basename(local)}')

# Now create a comprehensive script that:
# 1. Replaces logo files
# 2. Updates index.html (sidebar + title)
# 3. Updates login.html (login page)
# 4. Also copies to public/static (Django collectstatic serves from here)

with sftp.file('/tmp/rebrand.sh', 'w') as f:
    f.write('''#!/bin/bash
set -e
echo '=== BACKUP ORIGINAL FILES ==='
cp /usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html /tmp/index.html.bak
cp /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html /tmp/login.html.bak
echo 'Backed up'

echo ''
echo '=== FIND CYBER-PANEL-LOGO.SVG ==='
find /usr/local/CyberCP -name 'cyber-panel-logo.svg' 2>/dev/null
find /usr/local/CyberCP/public -name 'cyber-panel-logo.svg' 2>/dev/null

echo ''
echo '=== COPY LOGO TO STATIC DIRS ==='
# Copy as cyber-panel-logo.svg (same filename so templates auto-pick it up)
cp /tmp/zaydcluster-full-logo.svg /usr/local/CyberCP/public/static/baseTemplate/cyber-panel-logo.svg 2>/dev/null || true
cp /tmp/zaydcluster-full-logo.svg /usr/local/CyberCP/baseTemplate/static/baseTemplate/cyber-panel-logo.svg 2>/dev/null || true
echo 'Logo replaced'

echo ''
echo '=== COPY BANNER FOR LOGIN ==='
cp /tmp/zaydcluster-banner.svg /usr/local/CyberCP/public/static/images/zaydcluster-banner.svg 2>/dev/null || true
echo 'Banner copied'

echo ''
echo '=== UPDATE INDEX.HTML ==='
# Replace brand name and tagline in sidebar
sed -i 's/<div class="brand">CyberPanel<\\/div>/<div class="brand">ZaydCluster<\\/div>/g' /usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html
sed -i 's/<div class="tagline">Web Hosting Panel<\\/div>/<div class="tagline">Hosting Management<\\/div>/g' /usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html
# Replace page title
sed -i 's/{% block title %}CyberPanel{% endblock %}/{% block title %}ZaydCluster{% endblock %}/g' /usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html
# Replace social links text (Facebook YouTube X)
sed -i 's|https://web.facebook.com/groups/cyberpanel||g; s|https://www.youtube.com/@Cyber-Panel||g; s|https://x.com/CyberPanel||g' /usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html
echo 'Index.html updated'

echo ''
echo '=== UPDATE LOGIN.HTML ==='
# Replace title
sed -i 's|<title> Login - CyberPanel </title>|<title> Login - ZaydCluster </title>|g' /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html
# Replace meta description
sed -i 's|Login to your CyberPanel Account|Login to your ZaydCluster Account|g' /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html
# Replace heading text
sed -i 's|CyberPanel|ZaydCluster|g' /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html
# Replace banner image
sed -i 's|/static/images/cyberpanel-banner-graphics.png|/static/images/zaydcluster-banner.svg|g' /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html
# Replace heading text
sed -i 's|WEB HOSTING CONTROL PANEL|HOSTING MANAGEMENT|g' /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html
sed -i 's|FOR EVERYONE|by ZaydCluster|g' /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html
# Replace "Powered By" text
sed -i 's|Powered By OpenLiteSpeed/LiteSpeed Enterprise. Built For Speed, Security and|Powered by OpenLiteSpeed. Speed, Security and|g' /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html
sed -i 's|Reliability.|Reliability.|g' /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html
# Remove the changelogs link at bottom
sed -i '/change-logs/,/<\\/div>/d' /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html
sed -i '/changelogs/,/<\\/div>/d' /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html
echo 'Login.html updated'

echo ''
echo '=== COPY TO PUBLIC (collectstatic serves from here) ==='
cp /usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html /usr/local/CyberCP/public/baseTemplate/templates/baseTemplate/index.html 2>/dev/null || true
echo 'Copied to public'

echo ''
echo '=== RESTART CYBERPANEL ==='
systemctl restart lsws 2>/dev/null || true
echo 'LSWS restarted'

echo ''
echo '=== VERIFY ==='
echo 'Logo file:'
ls -la /usr/local/CyberCP/public/static/baseTemplate/cyber-panel-logo.svg 2>/dev/null
echo ''
echo 'Brand in index.html:'
grep -o 'class="brand">[^<]*' /usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html
echo ''
echo 'Title in index.html:'
grep -o 'block title.*endblock' /usr/local/CyberCP/baseTemplate/templates/baseTemplate/index.html | head -1
echo ''
echo 'Title in login.html:'
grep '<title>' /usr/local/CyberCP/loginSystem/templates/loginSystem/login.html | head -1
echo ''
echo '=== ALL DONE ==='
''')
sftp.chmod('/tmp/rebrand.sh', 0o755)
sftp.close()

channel = ssh.invoke_shell(width=200, height=50)
channel.settimeout(5)
channel.send('sudo bash /tmp/rebrand.sh\n')

output = ''
for _ in range(40):
    time.sleep(0.5)
    try:
        while channel.recv_ready():
            data = channel.recv(4096)
            output += data.decode(errors='replace')
    except: pass

print(output)
ssh.close()
