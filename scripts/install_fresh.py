import paramiko
import time
import sys

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

# Start fresh install with nohup
print("Starting aaPanel install...")
stdin, stdout, stderr = client.exec_command(
    "sudo bash -c 'nohup bash /tmp/aaPanel_en.sh aapanel > /tmp/aa_install.log 2>&1 &' && echo 'STARTED'",
    timeout=15
)
print(stdout.read().decode().strip())

# Get PID
time.sleep(3)
stdin, stdout, stderr = client.exec_command(
    "sudo pgrep -f 'aaPanel_en.sh' | head -1",
    timeout=10
)
pid = stdout.read().decode().strip()
print(f"Installer PID: {pid}")

# Monitor progress - check every 15s, max 8 min
start = time.time()
last_lines = 0

while time.time() - start < 480:
    time.sleep(15)
    
    # Check if still running
    stdin, stdout, stderr = client.exec_command(
        f"sudo kill -0 {pid} 2>/dev/null && echo RUNNING || echo DONE",
        timeout=10
    )
    status = stdout.read().decode().strip()
    
    # Check log size and last lines
    stdin, stdout, stderr = client.exec_command(
        "sudo wc -l < /tmp/aa_install.log 2>/dev/null; echo '|||'; sudo tail -3 /tmp/aa_install.log 2>/dev/null",
        timeout=10
    )
    log_info = stdout.read().decode().strip()
    
    elapsed = int(time.time() - start)
    print(f"[{elapsed}s] {status} | {log_info}")
    
    if "DONE" in status:
        print("\nINSTALLER FINISHED!")
        break

# Get final log
print("\n=== Final Installation Log ===")
stdin, stdout, stderr = client.exec_command(
    "sudo cat /tmp/aa_install.log 2>/dev/null",
    timeout=10
)
print(stdout.read().decode().strip())

# Verify
print("\n=== Verification ===")
for cmd in [
    "ls -la /www/server/panel/BT-Panel 2>/dev/null || echo 'BT-PANEL NOT FOUND'",
    "ps aux | grep BT- | grep -v grep | head -3",
    "ss -tlnp | grep -E '25095|36977|8888'",
]:
    stdin, stdout, stderr = client.exec_command(f"sudo {cmd}", timeout=10)
    print(stdout.read().decode().strip())

# Get credentials
print("\n=== Credentials ===")
for cmd in [
    "sudo cat /www/server/panel/data/default.pl 2>/dev/null",
    "sudo cat /www/server/panel/data/port.pl 2>/dev/null",
    "sudo cat /www/server/panel/data/admin_path.pl 2>/dev/null",
]:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    print(stdout.read().decode().strip())

client.close()
