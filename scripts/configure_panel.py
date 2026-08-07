import paramiko
import hashlib

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run_sudo(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(f"sudo bash -c '{cmd}'", timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# Step 1: Fix BT-Panel shebang to use our pyenv
print("=== Step 1: Fix BT-Panel shebang ===")
out, err = run_sudo("sed -i '1s@.*@#!/www/server/panel/pyenv/bin/python3@' /www/server/panel/BT-Panel && head -1 /www/server/panel/BT-Panel")
print(out)

# Step 2: Create SQLite database with default user  
print("\n=== Step 2: Create default.db ===")
out, err = run_sudo(
    "cd /www/server/panel && "
    "/www/server/panel/pyenv/bin/python3 -c \""
    "import sqlite3;"
    "db = sqlite3.connect('data/default.db');"
    "db.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT, password TEXT, phone TEXT, email TEXT, login_count INT, limit_access INT, status INT);');"
    "import hashlib;"
    "pwd_hash = hashlib.md5('Pro99@2026'.encode()).hexdigest();"
    "db.execute('DELETE FROM users');"
    "db.execute(\\\"INSERT INTO users(username,password,phone,email,login_count,limit_access,status) VALUES('ib0xgxtd','\" + pwd_hash + \"','','',0,0,1)\\\");"
    "db.commit();"
    "print('DB created, hash:', pwd_hash);"
    "db.close();"
    "\""
)
print(out or err)

# Step 3: Create system.db
print("\n=== Step 3: Create system.db ===")
out, err = run_sudo(
    "cd /www/server/panel && "
    "/www/server/panel/pyenv/bin/python3 -c \""
    "import sqlite3;"
    "db = sqlite3.connect('data/system.db');"
    "db.execute('CREATE TABLE IF NOT EXISTS site(id INTEGER PRIMARY KEY, name TEXT, path TEXT, status INT, addtime TEXT, edate TEXT, ps TEXT, pid TEXT, sid INT, stype TEXT, php_version TEXT, monitoring TEXT);');"
    "db.commit();"
    "print('system.db created');"
    "db.close();"
    "\""
)
print(out or err)

# Step 4: Set default password file
print("\n=== Step 4: Set default password file ===")
out, err = run_sudo("echo 'Pro99@2026' > /www/server/panel/default.pl")
print(out)

# Step 5: Ensure ssl.pl does NOT exist (disable SSL)
print("\n=== Step 5: Disable SSL ===")
out, err = run_sudo("rm -f /www/server/panel/data/ssl.pl && echo 'SSL DISABLED'")
print(out)

# Step 6: Create necessary directories and files
print("\n=== Step 6: Create dirs ===")
out, err = run_sudo(
    "mkdir -p /www/server/panel/logs && "
    "mkdir -p /www/server/panel/vhost/nginx && "
    "mkdir -p /www/server/panel/vhost/apache && "
    "mkdir -p /www/server/panel/data && "
    "chmod +x /www/server/panel/BT-Panel && "
    "chmod +x /www/server/panel/BT-Task && "
    "chmod -R 755 /www/server/panel/BTPanel/static 2>/dev/null || true && "
    "touch /www/server/panel/data/debug.pl && "
    "echo 'OK'"
)
print(out)

# Step 7: Kill any old processes
print("\n=== Step 7: Kill old processes ===")
out, err = run_sudo("pkill -f BT-Panel; pkill -f BT-Task; pkill -f webserver; sleep 1 && echo 'cleaned'")
print(out)

client.close()
