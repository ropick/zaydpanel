import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=10)

# Get full logs around the payment callback area
cmd = 'sudo docker logs zaydcluster-app 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
all_logs = stdout.read().decode()

lines = all_logs.split('\n')
# Print all lines from line 44 to 70 (around the callback)
print("=== FULL LOG around callback (lines 44-75) ===")
for i in range(43, min(76, len(lines))):
    print(f"  [{i}] {lines[i][:300]}")

ssh.close()
