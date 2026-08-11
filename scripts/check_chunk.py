import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Extract the provision-related section from the chunk
cmd = 'sudo docker exec zaydcluster-app grep -o ".{0,80}host.docker.internal.{0,80}" /app/.next/server/chunks/_0ltpzvg._.js 2>/dev/null'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
print("Around host.docker.internal:")
print(stdout.read().decode())

# Also check for username and password fields
cmd2 = 'sudo docker exec zaydcluster-app grep -o ".{0,60}username.{0,60}" /app/.next/server/chunks/_0ltpzvg._.js 2>/dev/null | head -5'
stdin, stdout, stderr = ssh.exec_command(cmd2, timeout=15)
stdin.channel.settimeout(15)
print("\nAround username:")
print(stdout.read().decode())

cmd3 = 'sudo docker exec zaydcluster-app grep -o ".{0,60}password.{0,60}" /app/.next/server/chunks/_0ltpzvg._.js 2>/dev/null | head -5'
stdin, stdout, stderr = ssh.exec_command(cmd3, timeout=15)
stdin.channel.settimeout(15)
print("\nAround password:")
print(stdout.read().decode())

# Check for the email send after provision
cmd4 = 'sudo docker exec zaydcluster-app grep -o ".{0,80}Hosting Aktif.{0,80}" /app/.next/server/chunks/_0ltpzvg._.js 2>/dev/null'
stdin, stdout, stderr = ssh.exec_command(cmd4, timeout=15)
stdin.channel.settimeout(15)
print("\nAround 'Hosting Aktif':")
print(stdout.read().decode())

# Check for Login Credentials  
cmd5 = 'sudo docker exec zaydcluster-app grep -o ".{0,80}Login Credentials.{0,80}" /app/.next/server/chunks/_0ltpzvg._.js 2>/dev/null'
stdin, stdout, stderr = ssh.exec_command(cmd5, timeout=15)
stdin.channel.settimeout(15)
print("\nAround 'Login Credentials':")
print(stdout.read().decode())

ssh.close()
