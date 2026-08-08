import paramiko

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run_sudo(cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(f"sudo bash -c '{cmd}'", timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# The BT-Panel is a Python Flask app. Let's check:
# 1. Where the webserver binary config handles SSL
# 2. The panel config for SSL
print("=== Webserver config ===")
out, err = run_sudo("cat /www/server/panel/webserver/tpls/webserver.conf 2>/dev/null")
print(out)

print("\n=== Webserver SSL config ===")
out, err = run_sudo("cat /www/server/panel/webserver/tpls/webserver_ssl.conf 2>/dev/null")
print(out)

print("\n=== Webserver listen config ===")
out, err = run_sudo("cat /www/server/panel/webserver/tpls/webserver_listen.conf 2>/dev/null")
print(out)

print("\n=== Webserver listen SSL config ===")
out, err = run_sudo("cat /www/server/panel/webserver/tpls/webserver_listen_ssl.conf 2>/dev/null")
print(out)

# Check main.py or similar
print("\n=== Main panel Python files ===")
out, err = run_sudo("ls /www/server/panel/*.py 2>/dev/null")
print(out)

# Check ssl.pl effect
print("\n=== SSL config files ===")
out, err = run_sudo("cat /www/server/panel/data/ssl.pl 2>/dev/null; echo ---; ls -la /www/server/panel/data/ssl* 2>/dev/null")
print(out)

client.close()
