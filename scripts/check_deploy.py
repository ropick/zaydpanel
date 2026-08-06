import paramiko, time

def connect():
    key = paramiko.RSAKey.from_private_key_file("/home/z/my-project/deploy/nusahost_id")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, code

client = connect()

# Check deploy log
out, _ = run(client, "cat /tmp/nusahost.log 2>/dev/null")
print(out)

# Check if still building
out2, _ = run(client, "ps aux | grep 'docker compose\\|docker build' | grep -v grep | head -5")
if out2:
    print("\n--- Still running ---")
    print(out2)
else:
    print("\n--- Container Status ---")
    out3, _ = run(client, "sudo docker compose -f /opt/nusahost/deploy/docker-compose.yml ps 2>&1")
    print(out3)
    print("\n--- Health ---")
    out4, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:3000 2>/dev/null")
    print(f"App: {out4}")
    out5, _ = run(client, "curl -s -o /dev/null -w 'HTTP %{http_code}' http://localhost:80 2>/dev/null")
    print(f"Nginx: {out5}")

client.close()
