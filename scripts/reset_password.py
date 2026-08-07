#!/usr/bin/env python3
"""Reset aaPanel admin password to a known value"""
import paramiko

def connect():
    key = paramiko.RSAKey.from_private_key_file("/home/z/my-project/deploy/nusahost_id")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=15):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

client = connect()

# Reset password using bt command
# bt 5 = change panel username
# bt 14 = change panel password (using CLI)

# Method: Use aaPanel's built-in password change via admin script
print("Resetting aaPanel password...")

# Use the bt CLI to set a new password
import hashlib
new_password = "Pro99@2026"
md5_pwd = hashlib.md5(new_password.encode()).hexdigest()
print(f"MD5 of new password: {md5_pwd}")

# Update the database directly
out, err, code = run(client, f"""sudo sqlite3 /www/server/panel/data/default.db "UPDATE users SET password='{md5_pwd}' WHERE username='ib0xgxtd';" 2>&1""")
print(f"Update result: {out} {err}")

# Verify
out, err, code = run(client, "sudo sqlite3 /www/server/panel/data/default.db 'SELECT username, password FROM users LIMIT 1;' 2>&1")
print(f"Verify: {out}")

client.close()
print(f"\n=== aaPanel Credentials ===")
print(f"URL: https://168.110.210.148:36977/613ccb60/")
print(f"Username: ib0xgxtd")
print(f"Password: {new_password}")
