import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# List docker volumes
print("=== Docker volumes ===")
stdin, stdout, stderr = ssh.exec_command('sudo docker volume ls 2>&1', timeout=10)
stdin.channel.settimeout(10)
print(stdout.read().decode().strip())

# Check compose project volumes
stdin, stdout, stderr = ssh.exec_command('sudo docker volume ls | grep -i deploy 2>&1', timeout=10)
stdin.channel.settimeout(10)
print(f"Deploy volumes: {stdout.read().decode().strip()}")

# The volume might have different name due to project name
stdin, stdout, stderr = ssh.exec_command('sudo docker volume ls --format "{{.Name}} | {{.Driver}}" 2>&1', timeout=10)
stdin.channel.settimeout(10)
vols = stdout.read().decode().strip()
print(f"\nAll volumes:\n{vols}")

ssh.close()
