import paramiko
import time

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run_sudo(cmd, timeout=300):
    stdin, stdout, stderr = client.exec_command(f"sudo bash -c '{cmd}'", timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# Step 1: Setup Python virtual environment for aaPanel
print("=== Step 1: Setup Python venv for aaPanel ===")
out, err = run_sudo(
    "python3 -m venv /www/server/panel/pyenv && "
    "/www/server/panel/pyenv/bin/pip install --upgrade pip 2>&1 | tail -3",
    timeout=120
)
print(out or err)

# Step 2: Install required Python packages
print("\n=== Step 2: Install Python packages ===")
packages = "flask flask-session gevent psutil pymongo pyopenssl requests cryptography pycparser cffi bcrypt"
out, err = run_sudo(
    f"/www/server/panel/pyenv/bin/pip install --no-cache-dir {packages} 2>&1 | tail -15",
    timeout=300
)
print(out or err)

# Step 3: Create data files
print("\n=== Step 3: Create config files ===")
cmds = [
    # Set port to 36977
    "echo '36977' > /www/server/panel/data/port.pl",
    # Create admin_path (security path)  
    "echo '/panel' > /www/server/panel/data/admin_path.pl",
    # Create SSL disabled marker
    "echo '0' > /www/server/panel/data/ssl.pl",
    # Create debug mode for local static files
    "touch /www/server/panel/data/debug.pl",
    # Set panel to HTTP mode (disable HTTPS redirect)
    "echo '0' > /www/server/panel/data/https_redirect.pl 2>/dev/null || true",
    # Make BT-Panel executable
    "chmod +x /www/server/panel/BT-Panel",
    "chmod +x /www/server/panel/BT-Task",
    # Set proper permissions
    "chmod -R 755 /www/server/panel/pyenv/bin",
    "chmod 600 /www/server/panel/BT-Panel",
    "chmod 700 /www/server/panel/pyenv/bin",
    "chown -R root:root /www/server/panel",
]

for cmd in cmds:
    out, err = run_sudo(cmd)
    if err and 'Warning' not in err:
        print(f"ERR: {cmd[:50]} => {err[:100]}")

print("Config files created OK")

# Step 4: Verify Python environment
print("\n=== Step 4: Verify Python ===")
out, err = run_sudo("/www/server/panel/pyenv/bin/python --version")
print(f"Python: {out}")

out, err = run_sudo("/www/server/panel/pyenv/bin/pip list 2>&1 | grep -iE 'flask|gevent|psutil|cryptography'")
print(f"Packages: {out}")

client.close()
