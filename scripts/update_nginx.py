import paramiko
import time

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# All HEAD requests return 500 - this is because panelSetup.init() returns None
# and BT-Panel HEAD method handler doesn't handle None return
# The GET actually works (200 with 181KB HTML)
# This is actually fine - browsers use GET not HEAD
# Let's update Docker nginx and test from outside

# Now update Docker nginx config to proxy to aaPanel
print("=== Updating Docker nginx config ===")

# Read current nginx config
out, err = run("sudo cat /opt/nusahost/deploy/nginx.conf 2>/dev/null | head -50")
print(f"Current config (first 50 lines):\n{out}")

client.close()
