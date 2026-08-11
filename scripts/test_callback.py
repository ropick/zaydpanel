import paramiko
import time

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Read the callback route.js to see which chunks it loads
cmd = 'sudo docker exec zaydcluster-app cat /app/.next/server/app/api/payment/callback/route.js 2>/dev/null'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
print("Callback route.js:")
print(stdout.read().decode())

# Now test the callback directly
print("\n=== Test callback endpoint ===")
cmd2 = 'sudo docker exec zaydcluster-app wget -qO- --post-data="{\\"status\\":\\"PAID\\",\\"external_id\\":\\"INV-TEST\\",\\"id\\":\\"test123\\"}" --header="Content-Type: application/json" --header="x-callback-token: test" http://localhost:3000/api/payment/callback 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd2, timeout=30)
stdin.channel.settimeout(30)
print(f"Response: {stdout.read().decode().strip()}")

# Check logs after test
time.sleep(3)
stdin, stdout, stderr = ssh.exec_command('sudo docker logs zaydcluster-app --tail 10 2>&1', timeout=15)
stdin.channel.settimeout(15)
print(f"\nLogs after test:\n{stdout.read().decode()}")

ssh.close()
