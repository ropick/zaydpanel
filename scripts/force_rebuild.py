import paramiko
import time

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Step 1: Clean everything and start build in background
print("=== Cleaning and starting build ===")
cmds = [
    'cd /opt/zaydcluster/deploy && sudo docker compose down --rmi all --volumes --remove-orphans 2>&1 || true',
    'sudo docker builder prune -af 2>&1 | tail -2',
    'sudo docker system prune -af 2>&1 | tail -2',
]

for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    stdin.channel.settimeout(60)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"  {out or err}")

# Start build in screen/tmux background
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/zaydcluster/deploy && sudo nohup sh -c "docker compose build --no-cache app > /tmp/zc-build.log 2>&1 && echo BUILD_OK >> /tmp/zc-build.log || echo BUILD_FAIL >> /tmp/zc-build.log" </dev/null >/dev/null 2>&1 &'
)
stdin.channel.settimeout(5)
try:
    stdout.read()
except:
    pass

print("  Build started in background. Waiting 180s...")

# Wait 3 minutes
time.sleep(180)

# Check if done
stdin, stdout, stderr = ssh.exec_command('tail -5 /tmp/zc-build.log 2>/dev/null', timeout=10)
stdin.channel.settimeout(10)
build_status = stdout.read().decode().strip()
print(f"\n  Build log tail:\n{build_status}")

if 'BUILD_OK' in build_status:
    print("\n=== BUILD SUCCESS! Starting container ===")
    stdin, stdout, stderr = ssh.exec_command('cd /opt/zaydcluster/deploy && sudo docker compose up -d 2>&1', timeout=60)
    stdin.channel.settimeout(60)
    print(stdout.read().decode().strip())
    
    time.sleep(8)
    
    # Verify
    stdin, stdout, stderr = ssh.exec_command(
        'sudo docker exec zaydcluster-app grep -c "creds.username" /app/.next/server/chunks/_0ltpzvg._.js 2>/dev/null || echo "0"',
        timeout=15
    )
    print(f"\ncreds.username in compiled code: {stdout.read().decode().strip()}")
    
    stdin, stdout, stderr = ssh.exec_command(
        'sudo docker exec zaydcluster-app grep -c "Login Panel" /app/.next/server/chunks/_0ltpzvg._.js 2>/dev/null || echo "0"',
        timeout=15
    )
    print(f"Login Panel in compiled code: {stdout.read().decode().strip()}")
    
    stdin, stdout, stderr = ssh.exec_command(
        'sudo docker ps --filter name=zaydcluster-app --format "{{.Names}} {{.Status}}"',
        timeout=15
    )
    print(f"Container: {stdout.read().decode().strip()}")
elif 'BUILD_FAIL' in build_status:
    print("\n!!! BUILD FAILED !!!")
    print(build_status)
else:
    print("\nBuild still running... check /tmp/zc-build.log on server")

ssh.close()
