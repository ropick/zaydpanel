import paramiko, sys

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()
sftp.put(
    '/home/z/my-project/zaydcluster-admin-fix/login-page.tsx',
    '/opt/zaydcluster/src/app/(auth)/login/page.tsx'
)
print('Login page uploaded')
sftp.close()
ssh.close()
