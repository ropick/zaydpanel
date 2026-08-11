import paramiko
import sys

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'
user = 'opc'

# Write a script on the remote server and execute it
remote_script = r'''
MYSQLPW=$(cat /etc/cyberpanel/mysqlPassword)
mysql -u root -p"$MYSQLPW" -e "SHOW DATABASES;" 2>&1
echo "=== WEBSITES ==="
mysql -u root -p"$MYSQLPW" cyberpanel -e "SELECT id, domain, state FROM websites;" 2>&1
echo "=== CP USERS ==="
mysql -u root -p"$MYSQLPW" cyberpanel -e "SELECT id, username, email FROM users;" 2>&1
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pkey = paramiko.Ed25519Key.from_private_key_file(key_path)

ssh.connect(host, username=user, pkey=pkey, timeout=15)

# Write script to remote tmp
sftp = ssh.open_sftp()
with sftp.file('/tmp/check_cp.sh', 'w') as f:
    f.write(remote_script)
sftp.chmod('/tmp/check_cp.sh', 0o755)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('bash /tmp/check_cp.sh', timeout=30)
print(stdout.read().decode())
err = stderr.read().decode().strip()
if err:
    print('STDERR:', err[:500])

ssh.close()
