import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Check provision-api service env
print("=== Provision API service config ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo cat /etc/systemd/system/provision-api.service',
    timeout=10
)
stdin.channel.settimeout(10)
print(stdout.read().decode())

# Verify PROVISION_SECRET consistency
print("\n=== Check PROVISION_SECRET in container (fallback) ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app node -e "console.log(process.env.PROVISION_SECRET || \'NOT_SET (will use fallback: zc-prov-2026-secret)\')"',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"  Container: {stdout.read().decode().strip()}")

stdin, stdout, stderr = ssh.exec_command(
    'sudo grep PROVISION_SECRET /etc/systemd/system/provision-api.service',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"  Service:  {stdout.read().decode().strip()}")

# Test provision with correct auth
print("\n=== Test provision API with auth ===")
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -X POST http://127.0.0.1:9999/provision -H "Content-Type: application/json" -H "Authorization: Bearer zc-prov-2026-secret" -d \'{"domain":"test.pro99.my.id","subdomain":"test-healthcheck","name":"HealthCheck","package":"Starter","email":"test@test.com","order":"HC-001"}\' 2>&1 | head -c 500',
    timeout=30
)
stdin.channel.settimeout(30)
print(f"  Response: {stdout.read().decode().strip()[:500]}")

ssh.close()
