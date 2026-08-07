import paramiko
import time

key_path = '/home/z/my-project/deploy/nusahost_id'
host = '168.110.210.148'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file(key_path, password=None)
client.connect(host, username='opc', pkey=key, timeout=15)

def run_sudo(cmd, timeout=30):
    """Run command with sudo"""
    stdin, stdout, stderr = client.exec_command(f"sudo bash -c '{cmd}'", timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err

def run(cmd, timeout=30):
    """Run command without sudo"""
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err

# STEP 1: Kill all aaPanel processes
print("=== STEP 1: Stop all aaPanel processes ===")
out, err = run_sudo("killall BT-Panel BT-Task 2>/dev/null; pkill -f BT-Panel; pkill -f BT-Task; sleep 2")
print(out)
if err: print(f"STDERR: {err}")

# Check if processes are gone
out, err = run("ps aux | grep -E 'BT-(Panel|Task)' | grep -v grep")
if out:
    print(f"WARNING - still running:\n{out}")
else:
    print("OK - All BT processes stopped")

# STEP 2: Remove /www directory completely
print("\n=== STEP 2: Remove /www directory ===")
out, err = run_sudo("rm -rf /www/server/panel /www/server/pannel /www/server/bt-*.tar.gz 2>/dev/null; ls -la /www/ 2>/dev/null || echo '/www removed or empty'")
print(out)
if err: print(f"STDERR: {err}")

# Also check for bt.py installer
out, err = run_sudo("rm -f /root/bt*.py /root/install*.sh /tmp/bt*.py 2>/dev/null; echo 'Cleaned up installer files'")
print(out)

# STEP 3: Check what's left
print("\n=== STEP 3: Verify cleanup ===")
out, err = run_sudo("ls -la /www/ 2>/dev/null || echo 'No /www directory'; ps aux | grep -E 'BT-|aapanel|bt\.cn' | grep -v grep || echo 'No BT processes'")
print(out)

# Check if port 36977 is free
out, err = run("ss -tlnp | grep 36977 || echo 'Port 36977 is FREE'")
print(out)

client.close()
print("\n=== CLEANUP COMPLETE ===")
