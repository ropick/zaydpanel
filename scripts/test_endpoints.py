import paramiko
import time

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# GET /login returns 200! HEAD /login returns 500 (that's fine, HEAD requests are not important)
# Let's test the code endpoint and login flow
print("=== Test endpoints ===")

for path in ["/login", "/code", "/userLang"]:
    out, err = run(f"sudo curl -sI --max-time 5 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977{path} 2>&1")
    # Get just the HTTP status line
    status = [l for l in out.split("\n") if "HTTP" in l]
    print(f"GET {path}: {status}")

# Test login page body size
out, err = run("sudo curl -s --max-time 10 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977/login 2>&1 | wc -c")
print(f"Login page size: {out} bytes")

# Check if login form is present
out, err = run("sudo curl -s --max-time 10 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977/login 2>&1 | grep -i 'password\\|username\\|input\\|login'")
print(f"Login form elements: {out[:500]}")

client.close()
