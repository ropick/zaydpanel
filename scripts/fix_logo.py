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

# Desktop navbar logo (exact match from lines 209-211)
old_desktop = """            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-emerald-500 flex items-center justify-center">
              <Server className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
            </div>"""

new_desktop = """            <img
              src="/logo-64.png"
              alt="ZaydCluster"
              className="w-8 h-8 sm:w-10 sm:h-10 rounded-full object-cover"
            />"""

count = content.count(old_desktop)
print(f"Found {count} occurrences of desktop logo block")

if count > 0:
    content = content.replace(old_desktop, new_desktop)
    print(f"Replaced {count} desktop logo blocks")

# Footer logo (exact match from lines 1142-1144, same pattern)
# Already replaced above if same pattern. Let's verify.
remaining_server_icons = content.count('Server className="w-5 h-5')
print(f"Remaining Server icon usages: {remaining_server_icons}")

with sftp.open(page_path, 'w') as f:
    f.write(content)

sftp.close()
ssh.close()
print("Done!")
