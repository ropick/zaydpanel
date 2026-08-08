import paramiko
import time

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
host = '168.110.210.148'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id', password=None)
client.connect(host, username='opc', pkey=key, timeout=15)

def run_sudo(cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(f"sudo bash -c '{cmd}'", timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# ===== MANUAL AAPANEL INSTALLATION =====
# Step 1: Create directory structure
print("=== Step 1: Create directories ===")
out, err = run_sudo("mkdir -p /www/server/panel/{data,logs,vhost,install,script,ssl,webserver,class,pyenv} && echo OK")
print(out)

# Step 2: Download panel zip directly
print("\n=== Step 2: Download aaPanel panel ===")
out, err = run_sudo(
    "wget --no-check-certificate -O /www/panel.zip "
    "'https://node.aapanel.com/install/src/panel_7_en.zip' "
    "-t 3 -T 120 2>&1 | tail -5",
    timeout=180
)
print(out)
if err: print(f"ERR: {err}")

# Step 3: Check download
out, err = run_sudo("ls -lh /www/panel.zip 2>/dev/null")
print(f"\nPanel zip: {out}")

# Step 4: Unzip
print("\n=== Step 3: Unzip panel ===")
out, err = run_sudo("cd /www && unzip -o panel.zip -d /www/server/ 2>&1 | tail -10", timeout=60)
print(out)

# Step 5: Verify
out, err = run_sudo("ls -la /www/server/panel/BT-Panel /www/server/panel/tools.py 2>/dev/null && echo PANEL_FILES_OK")
print(f"\nVerify: {out}")

client.close()
