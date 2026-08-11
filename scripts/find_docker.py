import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=10)

# Find docker-compose file and dockerfile
cmds = [
    'sudo find /opt/zaydcluster -maxdepth 2 -name "docker-compose*" -o -name "Dockerfile*" 2>/dev/null',
    'sudo ls -la /opt/zaydcluster/docker* 2>/dev/null',
    'sudo ls -la /opt/zaydcluster/*.yml /opt/zaydcluster/*.yaml 2>/dev/null',
]

for cmd in cmds:
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(out)
    if err:
        print(f"ERR: {err}")

ssh.close()
