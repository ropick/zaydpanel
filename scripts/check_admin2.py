import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Check admin login page and auth-options for admin credentials
sftp = ssh.open_sftp()

# Read auth-options to understand admin auth
print("=== auth-options ===")
try:
    with sftp.open('/opt/zaydcluster/src/lib/auth-options.ts', 'r') as f:
        content = f.read().decode()
    print(content[:3000])
except:
    print("File not found, searching...")
    stdin, stdout, stderr = ssh.exec_command(
        'sudo find /opt/zaydcluster/src -name "auth*" -type f 2>/dev/null',
        timeout=15
    )
    stdin.channel.settimeout(15)
    print(stdout.read().decode())

# Check login page for admin logic
print("\n=== Login page admin logic ===")
try:
    with sftp.open('/opt/zaydcluster/src/app/(auth)/login/page.tsx', 'r') as f:
        content = f.read().decode()
    # Find admin-related code
    for i, line in enumerate(content.split('\n')):
        if 'admin' in line.lower():
            start = max(0, i-2)
            end = min(len(content.split('\n')), i+5)
            for j in range(start, end):
                print(f"  [{j}] {content.split(chr(10))[j][:120]}")
            print("  ---")
except Exception as e:
    print(f"Error: {e}")

# Check if there's a register-admin or setup-admin endpoint
print("\n=== Admin setup endpoints ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo grep -rl "registerAdmin\\|setupAdmin\\|createAdmin\\|admin.*register" /opt/zaydcluster/src/ 2>/dev/null',
    timeout=15
)
stdin.channel.settimeout(15)
print(stdout.read().decode().strip() or "No admin setup endpoint found")

# Check auth register route for admin creation
print("\n=== Auth register route ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo cat /opt/zaydcluster/src/app/api/auth/register/route.ts 2>/dev/null | head -80',
    timeout=15
)
stdin.channel.settimeout(15)
print(stdout.read().decode()[:2000])

sftp.close()
ssh.close()
