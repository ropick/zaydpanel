import paramiko

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run_sudo(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(f"sudo bash -c '{cmd}'", timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# Check how ssl.pl is used in panel code
print("=== SSL usage in runserver.py ===")
out, err = run_sudo("cat /www/server/panel/runserver.py")
print(out)

print("\n=== SSL usage in runconfig.py ===")
out, err = run_sudo("cat /www/server/panel/runconfig.py")
print(out)

client.close()
