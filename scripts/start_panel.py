import paramiko
import time

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run_sudo(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(f"sudo bash -c '{cmd}'", timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# Step 1: Ensure ssl.pl is deleted (HTTP mode)
print("=== Step 1: Ensure SSL disabled ===")
out, err = run_sudo("rm -f /www/server/panel/data/ssl.pl && ls -la /www/server/panel/data/ssl.pl 2>&1 || echo 'ssl.pl removed'")
print(out)

# Step 2: Set port to 36977
print("\n=== Step 2: Set port 36977 ===")
out, err = run_sudo("echo '36977' > /www/server/panel/data/port.pl && cat /www/server/panel/data/port.pl")
print(out)

# Step 3: Ensure debug mode is on (local static files, no CDN)
print("\n=== Step 3: Debug mode ON ===")
out, err = run_sudo("touch /www/server/panel/data/debug.pl && ls -la /www/server/panel/data/debug.pl")
print(out)

# Step 4: Fix BT-Panel shebang
print("\n=== Step 4: Fix shebang ===")
out, err = run_sudo("sed -i '1s@.*@#!/www/server/panel/pyenv/bin/python3@' /www/server/panel/BT-Panel && head -1 /www/server/panel/BT-Panel")
print(out)

# Step 5: Set permissions
print("\n=== Step 5: Permissions ===")
out, err = run_sudo("chmod 700 /www/server/panel/BT-Panel && chmod 700 /www/server/panel/BT-Task && echo perms OK")
print(out)

# Step 6: Kill any existing panel processes
print("\n=== Step 6: Clean processes ===")
out, err = run_sudo("pkill -9 -f BT-Panel 2>/dev/null; pkill -9 -f BT-Task 2>/dev/null; pkill -9 -f webserver 2>/dev/null; sleep 1 && echo cleaned")
print(out)

# Step 7: Start BT-Panel
print("\n=== Step 7: Start BT-Panel ===")
out, err = run_sudo(
    "cd /www/server/panel && nohup /www/server/panel/BT-Panel > /www/server/panel/logs/panel.log 2>&1 &",
    timeout=10
)
print(f"Started: {out}")

# Step 8: Wait and check
time.sleep(3)
print("\n=== Step 8: Check process ===")
out, err = run_sudo("ps aux | grep BT-Panel | grep -v grep")
print(out or "NOT RUNNING")

# Step 9: Check port
out, err = run_sudo("ss -tlnp | grep 36977")
print(f"Port: {out}")

# Step 10: Check logs
print("\n=== Panel log ===")
out, err = run_sudo("tail -20 /www/server/panel/logs/panel.log 2>/dev/null")
print(out or err)

# Step 11: Test HTTP access locally
print("\n=== Test HTTP access ===")
out, err = run_sudo("curl -sI --max-time 5 -H 'User-Agent: Mozilla/5.0' http://127.0.0.1:36977/ 2>&1")
print(out or err)

# Step 12: Check if it's still redirecting to HTTPS
print("\n=== Test login page ===")
out, err = run_sudo("curl -s --max-time 5 -H 'User-Agent: Mozilla/5.0' http://127.0.0.1:36977/login 2>&1 | head -30")
print(out or err)

client.close()
