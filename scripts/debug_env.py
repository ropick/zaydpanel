import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Check .env permissions and content 
cmds = [
    'ls -la /opt/zaydcluster/.env',
    'sudo cat /opt/zaydcluster/.env | head -20',
    # Check if docker compose actually sees the env_file
    'cd /opt/zaydcluster/deploy && sudo docker compose config 2>&1 | grep -A 30 "environment"',
]

for cmd in cmds:
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    stdin.channel.settimeout(15)
    out = stdout.read().decode().strip()
    print(f"  {out[:1500]}")

ssh.close()
