import paramiko, time

def connect():
    key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('168.110.210.148', username='opc', pkey=key, timeout=15)
    return c

def run(c, cmd, timeout=60):
    stdin, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

c = connect()
print("=" * 55)
print("  FASE 3.2: Install aaPanel (Open Source Control Panel)")
print("=" * 55)

# Install aaPanel official script
# aaPanel supports AlmaLinux 9 ARM64
print("\n[1/4] Downloading aaPanel install script...")
out, err, code = run(c, "curl -sSO https://www.aapanel.com/script/install_6.0_en.sh 2>&1")
if code == 0:
    print("  Download OK")
else:
    print(f"  Download issue: {err}")

# Check the install options - aaPanel for AlmaLinux ARM64
# We'll use non-interactive install with predefined options
print("\n[2/4] Running aaPanel install (this takes 15-30 min)...")
print("  Stack: Nginx + MySQL 5.7 + PHP 8.x + Pure-FTPD + phpMyAdmin")
print("  (Running in background, will check progress...)\n")

# Install aaPanel with specific options via expect/background
install_cmd = """#!/bin/bash
cd /root
# Run aaPanel install non-interactively
# Options: Nginx, MySQL 5.7, PHP 8.1, Pure-FTPD
echo 'y' | bash install_6.0_en.sh \\
  --nginx \\
  --mysql 5.7 \\
  --php 81 \\
  --pureftpd \\
  --phpmyadmin \\
  2>&1
"""

# Write install script via SFTP
sftp = c.open_sftp()
with sftp.file('/tmp/aapanel_install.sh', 'w') as f:
    f.write(install_cmd)
sftp.chmod('/tmp/aapanel_install.sh', 0o755)
sftp.close()

# Run in background and log
run(c, "nohup bash /tmp/aapanel_install.sh > /tmp/aapanel-install.log 2>&1 &")

print("Install running in background...")
print("Monitoring progress...\n")

# Monitor progress
for i in range(6):
    time.sleep(10)
    out, _, _ = run(c, "tail -3 /tmp/aapanel-install.log 2>/dev/null")
    print(f"  [{i*10}s] {out.strip() if out.strip() else '(installing...)'}")

print("\n" + "=" * 55)
print("  Install is running in background (~15-30 minutes)")
print("=" * 55)
print("""
  Monitor: ssh opc@168.110.210.148 'tail -f /tmp/aapanel-install.log'

  After install complete, you will get:
  - aaPanel URL: http://168.110.210.148:8888/<random>
  - Username: (shown in log)
  - Password: (shown in log)

  NEXT STEPS after aaPanel is ready:
  1. Login aaPanel
  2. Install Node.js plugin (for Next.js)
  3. Create reverse proxy staging.pro99.my.id -> Docker :3000
  4. Create hosting packages for customers
  5. Install FOSSBilling
""")

c.close()
