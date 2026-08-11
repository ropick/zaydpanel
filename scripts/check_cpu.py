import paramiko
import sys

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'
user = 'opc'

commands = [
    "top -bn1 | head -20",
    "echo '===PROCESSES BY CPU==='",
    "ps aux --sort=-%cpu | head -15",
    "echo '===CPULIMIT STATUS==='",
    "systemctl status cpulimit-lswsgi 2>/dev/null || echo 'cpulimit service not found'",
    "echo '===LSWSGI PROCESSES==='",
    "ps aux | grep lswsgi | grep -v grep",
    "echo '===OPENLITESPEED==='",
    "ps aux | grep litespeed | grep -v grep",
    "echo '===LOAD AVG==='",
    "uptime",
    "echo '===MEMORY==='",
    "free -m",
    "echo '===DOCKER==='",
    "docker stats --no-stream 2>/dev/null || echo 'docker stats unavailable'",
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    pkey = paramiko.Ed25519Key.from_private_key_file(key_path)
except Exception as e:
    print(f"Failed to load key: {e}")
    sys.exit(1)

try:
    ssh.connect(host, username=user, pkey=pkey, timeout=15)
    for cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out:
            print(out)
        if err:
            print(f"STDERR: {err}")
        print()
except Exception as e:
    print(f"Connection error: {e}")
finally:
    ssh.close()
