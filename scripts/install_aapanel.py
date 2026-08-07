import paramiko
import time

key_path = '/home/z/my-project/deploy/nusahost_id'
host = '168.110.210.148'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file(key_path, password=None)
client.connect(host, username='opc', pkey=key, timeout=15)

def run_sudo(cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(f"sudo bash -c '{cmd}'", timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err

# Check OS and package manager
print("=== OS Info ===")
out, err = run_sudo("cat /etc/os-release | head -5; which yum dnf apt-get 2>/dev/null")
print(out)

# Install required dependencies
print("\n=== Installing dependencies ===")
out, err = run_sudo("dnf install -y wget curl python3 python3-devel python3-pip openssl-devel sqlite libffi-devel gcc make 2>&1 | tail -10")
print(out[-500:] if len(out) > 500 else out)
if err: print(f"ERR (last 300): {err[-300:]}")

# Download aaPanel official script
print("\n=== Downloading aaPanel installer ===")
out, err = run_sudo("cd /tmp && wget -O aaPanel_en.sh https://www.aapanel.com/script/new_install_en.sh --timeout=30 --tries=2 2>&1 | tail -5")
print(out)
if err: print(f"ERR: {err}")

# Check if downloaded
out, err = run_sudo("ls -la /tmp/aaPanel_en.sh && head -20 /tmp/aaPanel_en.sh")
print(out)

client.close()
