import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
k = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh.connect('168.110.210.148', username='opc', pkey=k)

fmt = '"%{http_code} %{size_download}"'

# Verify all logo files via HTTPS
files = [
    'https://staging.pro99.my.id/logo-64.png',
    'https://staging.pro99.my.id/favicon-32.png',
    'https://staging.pro99.my.id/favicon-16.png',
    'https://staging.pro99.my.id/logo-128.png',
    'https://staging.pro99.my.id/logo-256.png',
    'https://staging.pro99.my.id/apple-touch-icon.png',
    'https://staging.pro99.my.id/logo.svg',
]

print('=== ZaydCluster Circular Logo Files ===')
for url in files:
    s, o, _ = ssh.exec_command('curl -sk -o /dev/null -w ' + fmt + ' ' + url)
    r = o.read().decode().strip()
    fname = url.split('/')[-1]
    print('  %s -> %s' % (fname, r))

# Check CyberPanel
print('\n=== CyberPanel Circular Favicon ===')
s, o, _ = ssh.exec_command('curl -sk -o /dev/null -w ' + fmt + ' https://panel.pro99.my.id/favicon.png')
print('  CP Favicon -> %s' % o.read().decode().strip())

# Homepage test
fmt2 = '"%{http_code}"'
print('\n=== Site Health ===')
s, o, _ = ssh.exec_command('curl -sk -o /dev/null -w ' + fmt2 + ' https://staging.pro99.my.id/')
print('  Homepage: %s' % o.read().decode().strip())

s, o, _ = ssh.exec_command('curl -s -o /dev/null -w ' + fmt2 + ' http://localhost:3000/')
print('  App: %s' % o.read().decode().strip())

s, o, _ = ssh.exec_command('curl -sk -o /dev/null -w ' + fmt2 + ' https://panel.pro99.my.id/')
print('  CyberPanel: %s' % o.read().decode().strip())

ssh.close()
