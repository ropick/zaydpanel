import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh.connect('168.110.210.148', username='opc', pkey=key)

sftp = ssh.open_sftp()
local_dir = '/home/z/my-project/download/circle_logos'

# Upload ZaydCluster logos (owned by opc)
zayd_files = [
    ('logo-64.png', '/opt/zaydcluster/public/logo-64.png'),
    ('logo-128.png', '/opt/zaydcluster/public/logo-128.png'),
    ('logo-256.png', '/opt/zaydcluster/public/logo-256.png'),
    ('logo-1024.png', '/opt/zaydcluster/public/logo-full.png'),
    ('favicon-16.png', '/opt/zaydcluster/public/favicon-16.png'),
    ('favicon-32.png', '/opt/zaydcluster/public/favicon-32.png'),
    ('apple-touch-icon.png', '/opt/zaydcluster/public/apple-touch-icon.png'),
    ('logo-circle.svg', '/opt/zaydcluster/public/logo.svg'),
]

print("=== Uploading ZaydCluster logos ===")
for local_name, remote_path in zayd_files:
    local_path = os.path.join(local_dir, local_name)
    sftp.put(local_path, remote_path)
    print(f"  OK: {local_name} -> {remote_path}")

# Copy to /tmp first for CyberPanel, then sudo cp
cp_files = [
    ('cp-favicon.png', '/tmp/cp-favicon.png'),
    ('cp-logo-circle-190.png', '/tmp/cp-logo-circle-190.png'),
]

print("\n=== Uploading CyberPanel files to /tmp ===")
for local_name, remote_path in cp_files:
    local_path = os.path.join(local_dir, local_name)
    sftp.put(local_path, remote_path)
    print(f"  OK: {local_name} -> {remote_path}")

sftp.close()

# Now use sudo to copy CyberPanel files
cp_cmds = [
    'sudo cp /tmp/cp-favicon.png /usr/local/CyberCP/public/static/baseTemplate/assets/finalBase/favicon.png',
    'sudo cp /tmp/cp-favicon.png /usr/local/CyberCP/baseTemplate/static/baseTemplate/assets/finalBase/favicon.png',
    'sudo cp /tmp/cp-favicon.png /usr/local/CyberCP/public/static/baseTemplate/assets/images/icons/favicon.png',
    'sudo cp /tmp/cp-favicon.png /usr/local/CyberCP/baseTemplate/static/baseTemplate/assets/images/icons/favicon.png',
    'sudo cp /tmp/cp-logo-circle-190.png /usr/local/CyberCP/public/static/baseTemplate/assets/image-resources/logo.png',
    'sudo cp /tmp/cp-logo-circle-190.png /usr/local/CyberCP/baseTemplate/static/baseTemplate/assets/image-resources/logo.png',
    'sudo cp /tmp/cp-logo-circle-190.png /usr/local/CyberCP/public/static/baseTemplate/assets/image-resources/logo-alt.png',
    'sudo cp /tmp/cp-logo-circle-190.png /usr/local/CyberCP/baseTemplate/static/baseTemplate/assets/image-resources/logo-alt.png',
    'sudo cp /tmp/cp-logo-circle-190.png /usr/local/CyberCP/public/static/baseTemplate/assets/image-resources/logo-admin.png',
    'sudo cp /tmp/cp-logo-circle-190.png /usr/local/CyberCP/baseTemplate/static/baseTemplate/assets/image-resources/logo-admin.png',
]

print("\n=== Copying CyberPanel files with sudo ===")
for cmd in cp_cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if err:
        print(f"  ERR: {err}")
    else:
        fname = cmd.split('/')[-1]
        print(f"  OK: {fname}")

# Clear Django static cache and restart CyberPanel
stdin, stdout, stderr = ssh.exec_command('sudo systemctl restart lscpd 2>&1')
print("\n=== CyberPanel restart ===")
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
print("\n=== All uploads complete ===")
