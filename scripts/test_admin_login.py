import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Test admin login via API
print("=== Test admin login ===")
cmd = '''curl -s -X POST http://localhost:3000/api/auth/callback/credentials -H "Content-Type: application/json" -d '{"email":"ropickaplikasi@gmail.com","password":"Zayd12345","csrfToken":"dummy"}' 2>&1 | head -c 500'''
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
print(f"Login response: {stdout.read().decode().strip()}")

# Verify DB count
vol_path = '/var/lib/docker/volumes/deploy_app-data/_data'
stdin, stdout, stderr = ssh.exec_command(
    f'sudo sqlite3 {vol_path}/custom.db "SELECT COUNT(*) FROM User; SELECT COUNT(*) FROM Session; SELECT COUNT(*) FROM Invoice;" 2>&1',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"\nDB counts:\n{stdout.read().decode().strip()}")

ssh.close()
