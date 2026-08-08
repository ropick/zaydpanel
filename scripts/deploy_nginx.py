import paramiko
import time

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# Upload nginx.conf to VPS
sftp = client.open_sftp()
sftp.put('/home/z/my-project/deploy/nginx.conf', '/tmp/nginx.conf.new')
sftp.close()
print("nginx.conf uploaded")

# Copy to Docker volume and reload
out, err = run("sudo cp /tmp/nginx.conf.new /opt/nusahost/deploy/nginx.conf")
print(f"Copied: {out or err}")

# Reload Docker nginx
out, err = run("sudo docker exec nusahost-nginx nginx -t 2>&1")
print(f"Test config: {out or err}")

out, err = run("sudo docker exec nusahost-nginx nginx -s reload 2>&1")
print(f"Reload: {out or err}")

# Test via Docker nginx
time.sleep(2)
out, err = run("sudo curl -sI --max-time 10 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:80 -H 'Host: panel.pro99.my.id' /login 2>&1")
print(f"\nVia Docker nginx:")
print(out)

# Get body
out, err = run("sudo curl -s --max-time 10 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' -H 'Host: panel.pro99.my.id' http://127.0.0.1/login 2>&1 | wc -c")
print(f"Body size: {out} bytes")

client.close()
