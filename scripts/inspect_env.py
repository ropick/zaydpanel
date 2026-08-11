import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Method 1: docker inspect
print("=== docker inspect env ===")
cmd = 'sudo docker inspect zaydcluster-app --format "{{range .Config.Env}}{{println .}}{{end}}"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
envs = stdout.read().decode().strip()
count = 0
for line in envs.split('\n'):
    if any(k in line for k in ['GMAIL', 'PROVISION', 'XENDIT', 'NEXTAUTH', 'NODE_ENV', 'DATABASE', 'ADMIN']):
        print(f"  {line}")
        count += 1
if count == 0:
    print("  (no matching env vars found!)")
    print(f"  Total env count: {len(envs.split(chr(10)))}")
    # Show all envs
    for line in envs.split('\n')[:10]:
        print(f"    {line}")

# Method 2: env from inside container
print("\n=== env from inside container (printenv) ===")
cmd = 'sudo docker exec zaydcluster-app printenv 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
printenv_out = stdout.read().decode().strip()
for line in printenv_out.split('\n'):
    if any(k in line for k in ['GMAIL', 'PROVISION', 'XENDIT', 'NEXTAUTH', 'NODE_ENV', 'DATABASE', 'ADMIN']):
        print(f"  {line}")

ssh.close()
