import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)
sftp = ssh.open_sftp()

page_path = '/opt/zaydcluster/src/app/page.tsx'
with sftp.open(page_path, 'r') as f:
    content = f.read().decode()

# Footer logo - has extra indentation (16 spaces)
old_footer = """              <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
                <Server className="w-5 h-5 text-white" />
              </div>"""

new_footer = """              <img
                src="/logo-64.png"
                alt="ZaydCluster"
                className="w-8 h-8 rounded-full object-cover"
              />"""

if old_footer in content:
    content = content.replace(old_footer, new_footer)
    print("OK: Footer logo replaced")
else:
    print("WARNING: Footer logo not found with this pattern")

# Verify no more Server icon logos
remaining = content.count('Server className="w-5 h-5')
print(f"Remaining Server icon logos: {remaining}")

with sftp.open(page_path, 'w') as f:
    f.write(content)

sftp.close()
ssh.close()
