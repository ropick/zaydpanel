import paramiko
import time
import hashlib

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run_sudo(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(f"sudo bash -c '{cmd}'", timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# Step 1: Patch BT-Panel to disable HTTPS redirect
print("=== Step 1: Patch BT-Panel - disable HTTPS ===")
# Read BT-Panel to find HTTPS redirect code
out, err = run_sudo("head -50 /www/server/panel/BT-Panel")
print(out[:500])

# Step 2: Check the BT-Panel init.sh for SSL handling
print("\n=== Step 2: Check init.sh ===")
out, err = run_sudo("cat /www/server/panel/init.sh 2>/dev/null | head -50 || echo 'no init.sh'")
print(out[:500])

# Step 3: Check how panel handles SSL in Python code
print("\n=== Step 3: Find SSL redirect logic ===")
out, err = run_sudo("grep -rn 'https\\|ssl\\|SSL\\|redirect\\|302\\|SESSION_COOKIE' /www/server/panel/BT-Panel 2>/dev/null | head -20")
print(out)

client.close()
