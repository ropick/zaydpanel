import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Search ALL chunks for provision-related strings
keywords = ['host.docker.internal', 'provision', '9999', 'cpUsername', 'cpPassword',
            'Login Panel', 'Hosting Aktif', 'Login Credentials']

for kw in keywords:
    cmd = f'sudo docker exec zaydcluster-app grep -rl "{kw}" /app/.next/server/ 2>/dev/null'
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    stdin.channel.settimeout(30)
    files = stdout.read().decode().strip()
    if files:
        print(f"'{kw}' found in: {files}")
    else:
        print(f"'{kw}' NOT FOUND in any file")

ssh.close()
