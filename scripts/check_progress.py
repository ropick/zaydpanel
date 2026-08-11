import paramiko
import time

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Check build progress
stdin, stdout, stderr = ssh.exec_command('tail -3 /tmp/zc-build2.log 2>/dev/null; echo "---"; wc -l /tmp/zc-build2.log 2>/dev/null', timeout=15)
stdin.channel.settimeout(15)
print(f"Build progress:\n{stdout.read().decode().strip()}")

# Check if still running
stdin, stdout, stderr = ssh.exec_command('pgrep -af "buildkit" 2>/dev/null | head -2 || echo "No buildkit process"', timeout=15)
stdin.channel.settimeout(15)
print(f"\nBuild process: {stdout.read().decode().strip()}")

ssh.close()
