import paramiko
import time

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# The init() returns None, which is correct. Login function should handle that.
# The real issue is that Flask 2.2.5 doesn't match the login view code expectations
# Flask 3.x changed some behaviors. Let's upgrade Flask properly

print("=== Upgrading Flask ===")
out, err = run("sudo /www/server/panel/pyenv/bin/pip install --upgrade flask 2>&1 | tail -5")
print(out or err)

# Check version
out, err = run("sudo /www/server/panel/pyenv/bin/python3 -c 'import flask; print(flask.__version__)'")
print(f"Flask version: {out}")

# Restart panel
print("\n=== Restart ===")
run("sudo pkill -f BT-Panel 2>/dev/null; sudo pkill -f webserver 2>/dev/null")
time.sleep(2)
run("sudo bash -c 'cd /www/server/panel && nohup /www/server/panel/BT-Panel > /www/server/panel/logs/panel.log 2>&1 &'")
time.sleep(5)

out, err = run("sudo ps aux | grep BT-Panel | grep -v grep")
print(f"Process: {out or 'NOT RUNNING'}")

out, err = run("sudo curl -sI --max-time 5 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977/login 2>&1")
print(f"HTTP: {out}")

if '200' in out:
    print("\n=== PANEL IS WORKING! ===")
    out, err = run("sudo curl -s --max-time 5 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977/login 2>&1 | head -5")
    print(out)

client.close()
