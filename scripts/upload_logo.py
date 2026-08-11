import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)
sftp = ssh.open_sftp()

# Upload circular images to /opt/zaydcluster/public/
local_files = [
    '/home/z/my-project/upload/logo-64.png',
    '/home/z/my-project/upload/logo-128.png',
    '/home/z/my-project/upload/logo-256.png',
    '/home/z/my-project/upload/favicon-32.png',
    '/home/z/my-project/upload/favicon-16.png',
    '/home/z/my-project/upload/apple-touch-icon.png',
]

remote_dir = '/opt/zaydcluster/public/'
for local in local_files:
    fname = local.split('/')[-1]
    remote = remote_dir + fname
    print(f"Uploading {fname}...")
    sftp.put(local, remote)
    print(f"  OK: {remote}")

# Also copy the full-size original for general use
sftp.put('/home/z/my-project/upload/magnific_minimalist-and-modern-let_Xmt6lPlBfo.png', 
         remote_dir + 'logo-full.png')
print(f"  OK: {remote_dir}logo-full.png")

sftp.close()
ssh.close()
print("\nAll files uploaded!")
