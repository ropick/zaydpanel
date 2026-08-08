import paramiko
import time

key_path = '/home/z/my-project/deploy/nusahost_id'
host = '168.110.210.148'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file(key_path, password=None)
client.connect(host, username='opc', pkey=key, timeout=15)

# Step 1: Start installer in background, redirect output to log file
print("=== Starting aaPanel install (background) ===")
stdin, stdout, stderr = client.exec_command(
    "sudo nohup bash /tmp/aaPanel_en.sh aapanel > /tmp/aapanel_install.log 2>&1 & echo $!",
    timeout=15
)
pid = stdout.read().decode().strip()
print(f"Installer PID: {pid}")

# Step 2: Wait and monitor
for i in range(30):  # 30 iterations x 10s = 5 minutes max
    time.sleep(10)
    
    # Check if still running
    stdin, stdout, stderr = client.exec_command(
        f"sudo kill -0 {pid} 2>/dev/null && echo 'RUNNING' || echo 'DONE'",
        timeout=10
    )
    status = stdout.read().decode().strip()
    
    # Get last few lines of log
    stdin, stdout, stderr = client.exec_command(
        "sudo tail -3 /tmp/aapanel_install.log 2>/dev/null",
        timeout=10
    )
    log_tail = stdout.read().decode().strip()
    
    elapsed = (i + 1) * 10
    print(f"[{elapsed}s] Status: {status} | {log_tail}")
    
    if "DONE" in status:
        break

# Step 3: Get full log
print("\n=== Installation Log (last 50 lines) ===")
stdin, stdout, stderr = client.exec_command(
    "sudo tail -50 /tmp/aapanel_install.log 2>/dev/null",
    timeout=10
)
log = stdout.read().decode().strip()
print(log)

# Step 4: Verify installation
print("\n=== Post-Install Check ===")
checks = [
    ("BT-Panel exists", "ls -la /www/server/panel/BT-Panel 2>/dev/null || echo 'NOT FOUND'"),
    ("Processes", "ps aux | grep 'BT-' | grep -v grep | head -5"),
    ("Port", "ss -tlnp | grep -E '36977|8888|7681'"),
]
for label, cmd in checks:
    stdin, stdout, stderr = client.exec_command(f"sudo {cmd}", timeout=10)
    out = stdout.read().decode().strip()
    print(f"\n--- {label} ---")
    print(out)

# Get panel credentials
print("\n=== Panel Credentials ===")
for cmd in [
    "sudo cat /www/server/panel/data/default.pl 2>/dev/null || echo 'no default.pl'",
    "sudo cat /www/server/panel/data/port.pl 2>/dev/null",
    "sudo cat /www/server/panel/data/admin_path.pl 2>/dev/null",
]:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    out = stdout.read().decode().strip()
    print(out)

client.close()
