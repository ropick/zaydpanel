import paramiko
import time

key_path = '/home/z/my-project/deploy/nusahost_id'
host = '168.110.210.148'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file(key_path, password=None)
client.connect(host, username='opc', pkey=key, timeout=15)

def run_long(cmd, timeout=600):
    """Run a long command, read output until done"""
    transport = client.get_transport()
    channel = transport.open_session()
    channel.settimeout(timeout)
    channel.get_pty()
    channel.exec_command(f"sudo bash -c '{cmd}'")
    
    output = []
    start = time.time()
    
    while not channel.exit_status_ready() and (time.time() - start < timeout):
        if channel.recv_ready():
            data = channel.recv(4096).decode(errors='replace')
            output.append(data)
            print(data, end='', flush=True)
        if channel.recv_stderr_ready():
            data = channel.recv_stderr(4096).decode(errors='replace')
            output.append(data)
            print(data, end='', flush=True)
        time.sleep(0.3)
    
    # Read any remaining
    while channel.recv_ready():
        data = channel.recv(4096).decode(errors='replace')
        output.append(data)
        print(data, end='', flush=True)
    
    rc = channel.recv_exit_status()
    print(f"\n[Exit code: {rc}]")
    return ''.join(output), rc

# Run installer
print("=== Installing aaPanel ===")
print("(This takes 3-5 minutes on ARM VPS...)\n")

output, rc = run_long(
    "cd /tmp && bash aaPanel_en.sh aapanel 2>&1",
    timeout=600
)

# Post-install checks
print("\n=== Post-Install Verification ===")
def run_sudo(cmd, timeout=15):
    stdin, stdout, stderr = client.exec_command(f"sudo bash -c '{cmd}'", timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

for label, cmd in [
    ("BT-Panel", "ls -la /www/server/panel/BT-Panel 2>/dev/null || echo 'NOT FOUND'"),
    ("Processes", "ps aux | grep 'BT-' | grep -v grep"),
    ("Port", "ss -tlnp | grep -E '36977|8888|7681'"),
    ("Default Info", "cat /www/server/panel/data/default.pl 2>/dev/null || echo 'no default.pl'"),
    ("Panel Port", "cat /www/server/panel/data/port.pl 2>/dev/null || echo 'no port.pl'"),
    ("Admin Path", "cat /www/server/panel/data/admin_path.pl 2>/dev/null || echo 'no admin_path.pl'"),
    ("Username", "cat /www/server/panel/data/default.pl 2>/dev/null | head -1"),
    ("Password", "cat /www/server/panel/data/default.pl 2>/dev/null | tail -1"),
]:
    out, err = run_sudo(cmd)
    print(f"\n--- {label} ---")
    print(out if out else f"ERR: {err}")

client.close()
