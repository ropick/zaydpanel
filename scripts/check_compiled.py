import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=10)

# The actual code is in the chunk files - find which one has provision code
# Also check the source file in the build context
cmds = [
    # Check source file on disk (not in container) - the one we edited
    'sudo cat /opt/zaydcluster/src/app/api/payment/callback/route.ts 2>/dev/null | grep -c "host.docker.internal"',
    'sudo cat /opt/zaydcluster/src/app/api/payment/callback/route.ts 2>/dev/null | grep -c "provision"',
    'sudo cat /opt/zaydcluster/src/app/api/payment/callback/route.ts 2>/dev/null | grep -c "creds.username"',
    # Check compiled chunks
    'sudo docker exec zaydcluster-app grep -rl "host.docker.internal" /app/.next/ 2>/dev/null',
    'sudo docker exec zaydcluster-app grep -rl "creds.username" /app/.next/ 2>/dev/null',
]

for cmd in cmds:
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"  => {out or err}")

ssh.close()
