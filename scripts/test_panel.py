import paramiko
import time

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# Restart panel
run("sudo pkill -f BT-Panel 2>/dev/null; sudo pkill -f webserver 2>/dev/null")
time.sleep(2)
run("sudo bash -c 'cd /www/server/panel && nohup /www/server/panel/BT-Panel > /www/server/panel/logs/panel.log 2>&1 &'")
time.sleep(5)

out, err = run("sudo curl -sI --max-time 5 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977/login 2>&1")
print(f"HTTP Headers:\n{out}")

out, err = run("sudo curl -s --max-time 5 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977/login 2>&1 | head -10")
print(f"Body: {out[:500]}")

out, err = run("sudo tail -5 /www/server/panel/logs/error.log 2>/dev/null")
print(f"Error: {err or out}")

client.close()
