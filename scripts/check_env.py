import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

sftp = ssh.open_sftp()

# Check .env file
print("=== Checking .env file ===")
try:
    with sftp.open('/opt/zaydcluster/.env', 'r') as f:
        env_content = f.read().decode()
    # Show keys (not values)
    lines = env_content.strip().split('\n')
    for line in lines:
        if '=' in line:
            key = line.split('=')[0]
            val = line.split('=', 1)[1]
            masked = val[:5] + '...' if len(val) > 5 else 'SET'
            print(f"  {key} = {masked}")
        else:
            print(f"  {line}")
except Exception as e:
    print(f"  ERROR reading .env: {e}")

# Check if env_file path is correct in docker-compose
print("\n=== docker-compose env_file config ===")
with sftp.open('/opt/zaydcluster/deploy/docker-compose.yml', 'r') as f:
    dc = f.read().decode()
for line in dc.split('\n'):
    if 'env_file' in line or '.env' in line:
        print(f"  {line}")

# Check .env relative to deploy/ dir
print("\n=== Check .env exists relative to deploy/ ===")
cmds = [
    'ls -la /opt/zaydcluster/deploy/../.env 2>&1',
    'ls -la /opt/zaydcluster/.env 2>&1',
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    stdin.channel.settimeout(10)
    print(f"  {stdout.read().decode().strip()}")

sftp.close()
ssh.close()
