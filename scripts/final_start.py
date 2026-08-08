import paramiko
import time

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# Wait for remaining pip install to finish
print("Waiting for background pip to finish...")
time.sleep(5)
out, err = run("sudo kill 185890 2>/dev/null; echo done")

# Apply all fixes
print("=== Fix 1: Type annotations ===")
run("sudo sed -i 's/from typing import /from typing import Union, Set, /' /www/server/panel/class/public/common.py")
run("sudo sed -i 's/dict | List\\[dict\\]/Union[dict, List[dict]]/g' /www/server/panel/class/public/common.py")
run("sudo sed -i 's/List\\[str\\] | Set\\[str\\]/Union[List[str], Set[str]]/g' /www/server/panel/class/public/common.py")

print("=== Fix 2: Shebang ===")
run("sudo sed -i '1s@.*@#!/www/server/panel/pyenv/bin/python3@' /www/server/panel/BT-Panel")

print("=== Fix 3: SSL disabled ===")
run("sudo rm -f /www/server/panel/data/ssl.pl")

print("=== Fix 4: Debug mode ===")
run("sudo touch /www/server/panel/data/debug.pl")

print("=== Fix 5: Port ===")
run("sudo bash -c 'echo 36977 > /www/server/panel/data/port.pl'")

print("=== Fix 6: Permissions ===")
run("sudo chmod 700 /www/server/panel/BT-Panel")
run("sudo chmod 700 /www/server/panel/BT-Task")

print("=== Fix 7: Clean processes ===")
run("sudo pkill -f BT-Panel 2>/dev/null")
run("sudo pkill -f BT-Task 2>/dev/null")
run("sudo pkill -f webserver 2>/dev/null")
time.sleep(1)

print("=== Starting BT-Panel ===")
out, err = run("sudo bash -c 'cd /www/server/panel && nohup /www/server/panel/BT-Panel > /www/server/panel/logs/panel.log 2>&1 &'")
time.sleep(5)

# Check status
out, err = run("sudo ps aux | grep BT-Panel | grep -v grep")
print(f"Process: {out or 'NOT RUNNING'}")

if not out:
    out, err = run("sudo tail -30 /www/server/panel/logs/panel.log")
    print(f"Log: {out}")
else:
    # Check port
    out, err = run("sudo ss -tlnp | grep 36977")
    print(f"Port: {out or 'NOT LISTENING'}")
    
    if 'LISTEN' in (out or ''):
        # Test HTTP access
        out, err = run("sudo curl -sI --max-time 5 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977/login 2>&1")
        print(f"HTTP Response: {out}")

client.close()
