import paramiko, sys, os

key = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

sftp = ssh.open_sftp()

# Map: local_file -> remote_file
base = '/home/z/my-project'
files = {
    f'{base}/zaydcluster-admin-fix/layout.tsx': '/opt/zaydcluster/src/app/(admin)/layout.tsx',
    f'{base}/zaydcluster-admin-fix/admin-page.tsx': '/opt/zaydcluster/src/app/(admin)/admin/page.tsx',
    f'{base}/zaydcluster-admin-fix/orders-page.tsx': '/opt/zaydcluster/src/app/(admin)/admin/orders/page.tsx',
    f'{base}/zaydcluster-admin-fix/invoices-page.tsx': '/opt/zaydcluster/src/app/(admin)/admin/invoices/page.tsx',
    f'{base}/zaydcluster-admin-fix/customers-page.tsx': '/opt/zaydcluster/src/app/(admin)/admin/customers/page.tsx',
    f'{base}/zaydcluster-admin-fix/profile-page.tsx': '/opt/zaydcluster/src/app/(admin)/admin/profile/page.tsx',
    f'{base}/zaydcluster-admin-fix/profile-route.ts': '/opt/zaydcluster/src/app/api/admin/profile/route.ts',
}

# Create directories
dirs = [
    '/opt/zaydcluster/src/app/(admin)/admin/profile',
    '/opt/zaydcluster/src/app/api/admin/profile',
]
for d in dirs:
    try:
        sftp.stat(d)
    except:
        sftp.mkdir(d)
        print(f'Created dir: {d}')

for local, remote in files.items():
    print(f'Uploading: {os.path.basename(local)} -> {remote}')
    sftp.put(local, remote)
    print(f'  OK')

sftp.close()
ssh.close()
print('\nAll files uploaded successfully!')
