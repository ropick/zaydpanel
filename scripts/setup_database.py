import paramiko

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

# Simpler database setup - just create table without specifying columns
db_script = """#!/www/server/panel/pyenv/bin/python3
import sqlite3
import hashlib
import os
os.chdir('/www/server/panel')

# Remove old db first
import glob
for f in glob.glob('data/default.db*'):
    os.remove(f)

db = sqlite3.connect('data/default.db')
# Create with all columns
c = db.cursor()
c.execute('CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, password TEXT, phone TEXT, email TEXT, login_count INTEGER DEFAULT 0, limit_access INTEGER DEFAULT 0, status INTEGER DEFAULT 1)')
pwd_hash = hashlib.md5('Pro99@2026'.encode()).hexdigest()
c.execute('INSERT INTO users(username,password,phone,email,login_count,limit_access,status) VALUES(?,?,?,?,?,?,?)', ('ib0xgxtd', pwd_hash, '', '', 0, 0, 1))
db.commit()
# Verify
c.execute('SELECT * FROM users')
row = c.fetchone()
print('DB OK: user=%s hash=%s' % (row[1], row[2]))
db.close()

# System db
for f in glob.glob('data/system.db*'):
    os.remove(f)
db2 = sqlite3.connect('data/system.db')
db2.execute('CREATE TABLE site(id INTEGER PRIMARY KEY, name TEXT, path TEXT, status INTEGER, addtime TEXT, edate TEXT, ps TEXT)')
db2.commit()
db2.close()
print('All DBs created')
"""

sftp = client.open_sftp()
with sftp.file('/tmp/setup_db.py', 'w') as f:
    f.write(db_script)
sftp.close()

stdin, stdout, stderr = client.exec_command(
    'sudo /www/server/panel/pyenv/bin/python3 /tmp/setup_db.py',
    timeout=15
)
print(stdout.read().decode().strip())
err = stderr.read().decode().strip()
if err:
    print(f"ERR: {err}")

client.close()
