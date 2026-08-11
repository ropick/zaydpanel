import paramiko
import time

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=10)

print("=== Rebuilding Docker container ===")
cmd = 'cd /opt/zaydcluster/deploy && sudo docker compose up -d --build'
print(f"Running: {cmd}")
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=300)
out = stdout.read().decode()
err = stderr.read().decode()
if out:
    print(out[-3000:] if len(out) > 3000 else out)
if err:
    print("STDERR:", err[-3000:] if len(err) > 3000 else err)

print("\n=== Waiting 10s for container to stabilize ===")
time.sleep(10)

print("\n=== Container status ===")
stdin, stdout, stderr = ssh.exec_command('sudo docker ps --filter name=zaydcluster-app --format "{{.Names}} {{.Status}}"', timeout=15)
print(stdout.read().decode().strip())

print("\n=== Container logs (last 20 lines) ===")
stdin, stdout, stderr = ssh.exec_command('sudo docker logs zaydcluster-app --tail 20 2>&1', timeout=15)
print(stdout.read().decode())

ssh.close()
print("Done!")
