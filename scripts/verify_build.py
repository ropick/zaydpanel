import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=10)

# Check what files exist for the callback route and search for credential strings
cmds = [
    'sudo docker exec zaydcluster-app find /app/.next -name "route.js" -path "*callback*" 2>/dev/null',
    'sudo docker exec zaydcluster-app grep -rl "creds.username\|creds.password\|cpUsername" /app/.next/server/ 2>/dev/null | head -10',
    'sudo docker exec zaydcluster-app grep -rl "Login Panel\|hostingReady" /app/.next/ 2>/dev/null | head -10',
]

for cmd in cmds:
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"  => {out or err}")

ssh.close()
