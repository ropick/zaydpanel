import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

vol_path = '/var/lib/docker/volumes/deploy_app-data/_data'
pw_hash = '$2a$12$FdxtRc2IcIRAjO3sks417eKjqf55398D8e6Bs.Qs1tXO8zozaI92S'

# Use a SQL file to avoid shell escaping issues
sftp = ssh.open_sftp()

admin_sql = f"""INSERT OR IGNORE INTO User (id, email, name, phone, password, role) 
VALUES ('admin-001', 'ropickaplikasi@gmail.com', 'Administrator', '081234567890', '{pw_hash}', 'admin');
"""

with sftp.open('/tmp/admin.sql', 'w') as f:
    f.write(admin_sql)

stdin, stdout, stderr = ssh.exec_command(
    f'sudo sqlite3 {vol_path}/custom.db < /tmp/admin.sql 2>&1',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"Insert: {stdout.read().decode().strip() or stderr.read().decode().strip()}")

# Verify
stdin, stdout, stderr = ssh.exec_command(
    f'sudo sqlite3 {vol_path}/custom.db "SELECT id, email, role FROM User;" 2>&1',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"Users: {stdout.read().decode().strip()}")

# Fix permissions
stdin, stdout, stderr = ssh.exec_command(f'sudo chown 1001:1001 {vol_path}/custom.db 2>&1', timeout=10)
stdin.channel.settimeout(10)

sftp.close()
ssh.close()
