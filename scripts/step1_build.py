import paramiko
import time

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# The real fix: just delete the build cache inside the container build context
# and also .next folder from source before building
print("=== Delete .next cache from source, then rebuild ===")
cmds = [
    ('sudo rm -rf /opt/zaydcluster/.next 2>/dev/null; echo "cleared .next"', 10),
    ('sudo rm -rf /opt/zaydcluster/node_modules/.cache 2>/dev/null; echo "cleared node_modules cache"', 10),
    ('cd /opt/zaydcluster/deploy && sudo docker compose stop app 2>&1', 30),
    ('cd /opt/zaydcluster/deploy && sudo docker compose rm -f app 2>&1', 30),
]

for cmd, t in cmds:
    print(f"  {cmd[:70]}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=t)
    stdin.channel.settimeout(t)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"  => {out or err}")

print("\n=== Starting no-cache build in background ===")
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/zaydcluster/deploy && sudo nohup sh -c "docker compose build --no-cache app > /tmp/zc-build2.log 2>&1 && echo BUILD_OK >> /tmp/zc-build2.log || echo BUILD_FAIL >> /tmp/zc-build2.log" </dev/null >/dev/null 2>&1 &',
    timeout=10
)
stdin.channel.settimeout(10)
try:
    stdout.read()
except:
    pass
print("  Build started. Check with step2 script in ~3 min.")

ssh.close()
