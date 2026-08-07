import paramiko
import sys

key_path = '/home/z/my-project/deploy/nusahost_id'
host = '168.110.210.148'

# Try with password auth disabled, various key formats
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # Try loading key with explicit passphrase=None
    key = paramiko.RSAKey.from_private_key_file(key_path, password=None)
    print(f"Key loaded: {key.get_name()} {key.get_bits()} bits")
    
    client.connect(host, username='root', pkey=key, timeout=15, banner_timeout=15, auth_timeout=15)
    print("Connected!")
    
    # Quick test
    stdin, stdout, stderr = client.exec_command('whoami && hostname', timeout=10)
    print(stdout.read().decode().strip())
    client.close()
except paramiko.AuthenticationException as e:
    print(f"Auth failed: {e}")
    # Try with different username
    for user in ['oracle', 'opc']:
        try:
            client.connect(host, username=user, pkey=key, timeout=15, banner_timeout=15)
            print(f"Connected as {user}!")
            stdin, stdout, stderr = client.exec_command('whoami && hostname', timeout=10)
            print(stdout.read().decode().strip())
            client.close()
            break
        except Exception as e2:
            print(f"Failed as {user}: {e2}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
