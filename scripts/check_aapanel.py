import paramiko

key_path = '/home/z/my-project/deploy/nusahost_id'
host = '168.110.210.148'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

key = paramiko.RSAKey.from_private_key_file(key_path, password=None)

# Connect as opc
client.connect(host, username='opc', pkey=key, timeout=15)
print("Connected as opc")

# Run diagnostic commands
commands = [
    ("BT-Panel Process", "ps aux | grep 'BT-Panel' | grep -v grep"),
    ("BT-Task Process", "ps aux | grep 'BT-Task' | grep -v grep"),
    ("CPU Top", "top -bn1 | head -15"),
    ("Port 36977", "ss -tlnp | grep 36977"),
    ("Memory", "free -h"),
    ("Disk", "df -h /"),
    ("Curl Panel Page", "curl -s -o /dev/null -w 'HTTP_CODE:%{http_code} TIME:%{time_total}s SIZE:%{size_download}' --max-time 15 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977/613ccb60/"),
    ("Curl Code Endpoint", "curl -s -o /dev/null -w 'HTTP_CODE:%{http_code} TIME:%{time_total}s' --max-time 10 -H 'User-Agent: Mozilla/5.0' http://127.0.0.1:36977/code"),
    ("Curl UserLang Endpoint", "curl -s -o /dev/null -w 'HTTP_CODE:%{http_code} TIME:%{time_total}s' --max-time 10 -H 'User-Agent: Mozilla/5.0' http://127.0.0.1:36977/userLang"),
    ("Panel Error Log", "tail -20 /www/server/panel/logs/error.log 2>/dev/null || echo 'No error log'"),
    ("BT-Panel executable", "ls -la /www/server/panel/BT-Panel"),
    ("BT-Task executable", "ls -la /www/server/panel/BT-Task"),
]

for label, cmd in commands:
    print(f"\n=== {label} ===")
    try:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out:
            print(out)
        if err:
            print(f"STDERR: {err}")
    except Exception as e:
        print(f"ERROR: {e}")

client.close()
