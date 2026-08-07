import paramiko
import time

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# Fix: create sites table in system.db (the panel code expects it)
db_fix = """import sqlite3, os
os.chdir('/www/server/panel')
db = sqlite3.connect('data/system.db')
db.execute('CREATE TABLE IF NOT EXISTS sites(id INTEGER PRIMARY KEY, name TEXT, path TEXT, status INTEGER, addtime TEXT, edate TEXT, ps TEXT, pid TEXT, sid INTEGER, stype TEXT, php_version TEXT, monitoring TEXT)')
db.execute('CREATE TABLE IF NOT EXISTS databases(id INTEGER PRIMARY KEY, name TEXT, db_user TEXT, db_type TEXT, pid INTEGER, ps TEXT, addtime TEXT, status INTEGER)')
db.commit()
print('Tables created')
db.close()
"""

# Upload and run
sftp = client.open_sftp()
with sftp.file('/tmp/fix_tables.py', 'w') as f:
    f.write(db_fix)
sftp.close()

out, err = run("sudo /www/server/panel/pyenv/bin/python3 /tmp/fix_tables.py")
print(f"DB Fix: {out}")

# Restart BT-Panel
print("\n=== Restarting BT-Panel ===")
run("sudo pkill -f BT-Panel 2>/dev/null")
run("sudo pkill -f webserver 2>/dev/null")
time.sleep(2)

out, err = run("sudo bash -c 'cd /www/server/panel && nohup /www/server/panel/BT-Panel > /www/server/panel/logs/panel.log 2>&1 &'")
time.sleep(5)

out, err = run("sudo ps aux | grep BT-Panel | grep -v grep")
print(f"Process: {out or 'NOT RUNNING'}")

out, err = run("sudo ss -tlnp | grep 36977")
print(f"Port: {out or 'NOT LISTENING'}")

if 'LISTEN' in (out or ''):
    # Test login page
    out, err = run("sudo curl -s --max-time 5 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977/login 2>&1 | head -20")
    print(f"Login page: {out[:500]}")
    
    # Test with response headers
    out, err = run("sudo curl -sI --max-time 5 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977/login 2>&1")
    print(f"Headers: {out}")

client.close()
