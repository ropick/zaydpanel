import paramiko
import sys
import json

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'
user = 'opc'

commands = [
    # Step 1: List CyberPanel websites to find the one to delete
    "echo '=== LIST WEBSITES ==='",
    "docker exec zaydcluster-app node -e \"const {PrismaClient}=require('@prisma/client');const p=new PrismaClient();p.order.findMany({select:{id,cpUsername,cpDomain,packageName,email}}).then(r=>console.log(JSON.stringify(r,null,2)))\"",
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    pkey = paramiko.Ed25519Key.from_private_key_file(key_path)
except Exception as e:
    print(f"Failed to load key: {e}")
    sys.exit(1)

try:
    ssh.connect(host, username=user, pkey=pkey, timeout=15)
    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out:
            print(out)
        if err:
            print(f"STDERR: {err}")
        print()
except Exception as e:
    print(f"Connection error: {e}")
finally:
    ssh.close()
