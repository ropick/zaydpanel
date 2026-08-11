import paramiko
import time

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

print("=== Starting no-cache build ===")
transport = ssh.get_transport()
transport.set_keepalive(30)

# Start build in background on server
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/zaydcluster/deploy && sudo nohup sh -c "docker compose build --no-cache app > /tmp/build.log 2>&1" </dev/null &\necho BUILD_STARTED',
    timeout=10
)
stdin.channel.settimeout(5)
try:
    out = stdout.read().decode().strip()
    print(out)
except:
    print("(started)")

print("Monitoring build progress...\n")

for i in range(50):
    time.sleep(20)
    try:
        stdin, stdout, stderr = ssh.exec_command(
            'wc -l /tmp/build.log 2>/dev/null && tail -1 /tmp/build.log 2>/dev/null',
            timeout=10
        )
        stdin.channel.settimeout(10)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        print(f"  [{(i+1)*20}s] {out[:150]}")
    except Exception as e:
        print(f"  [{(i+1)*20}s] read error")

    # Check if build still running
    try:
        stdin, stdout, stderr = ssh.exec_command(
            'pgrep -f "buildkit" > /dev/null 2>&1 && echo RUNNING || echo DONE',
            timeout=10
        )
        stdin.channel.settimeout(10)
        status = stdout.read().decode().strip()
        if 'DONE' in status:
            print(f"\n  Build finished after {(i+1)*20}s!")
            stdin, stdout, stderr = ssh.exec_command('tail -5 /tmp/build.log', timeout=10)
            stdin.channel.settimeout(10)
            print(stdout.read().decode())
            break
    except:
        pass

ssh.close()
print("\nMonitoring done.")
