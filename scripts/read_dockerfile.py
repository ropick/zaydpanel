import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=10)

sftp = ssh.open_sftp()
with sftp.open('/opt/zaydcluster/deploy/Dockerfile', 'r') as f:
    print(f.read().decode())
sftp.close()
ssh.close()
