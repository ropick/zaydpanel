import paramiko
import time

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run(cmd, timeout=300):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# Install packages
print("=== Installing packages ===")
pkgs = "flask flask-session gevent psutil pymongo pyopenssl requests cryptography pycparser cffi bcrypt pyinotify"
out, err = run(f"sudo /www/server/panel/pyenv/bin/pip install --no-cache-dir {pkgs}")
# Show last few lines
lines = out.strip().split("\n")
for l in lines[-8:]:
    print(l)

# Fix shebang
print("\n=== Fix shebang ===")
out, err = run("sudo sed -i '1s@.*@#!/www/server/panel/pyenv/bin/python3@' /www/server/panel/BT-Panel")
print("Done")

# Fix type annotations
print("\n=== Fix types ===")
out, err = run("sudo sed -i 's/from typing import /from typing import Union, Set, /' /www/server/panel/class/public/common.py")
out, err = run("sudo sed -i 's/dict | List\\[dict\\]/Union[dict, List[dict]]/g' /www/server/panel/class/public/common.py")
out, err = run("sudo sed -i 's/List\\[str\\] | Set\\[str\\]/Union[List[str], Set[str]]/g' /www/server/panel/class/public/common.py")
print("Done")

# Verify python
out, err = run("sudo /www/server/panel/pyenv/bin/python3 --version")
print(f"\nPython: {out}")

# Test BT-Panel import
print("\n=== Test BT-Panel import ===")
out, err = run("sudo /www/server/panel/pyenv/bin/python3 -c 'import sys; sys.path.insert(0,\"/www/server/panel\"); print(\"Import OK\")' 2>&1")
print(out or err)

client.close()
