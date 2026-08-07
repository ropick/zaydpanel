#!/usr/bin/env python3
"""Find and restore the REAL common.py - it's in class/ directory"""
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
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

client = connect()

# 1. Find the REAL common.py location
print("[1] Find common.py locations...")
out, err, code = run(client, "sudo find /www/server/panel -maxdepth 3 -name 'common.py' -not -path '*/pyenv/*' -not -path '*/__pycache__/*' 2>/dev/null")
print(f"  Files: {out}")

# 2. Check if it exists in class/
out, err, code = run(client, "sudo ls -la /www/server/panel/class/common.py 2>&1")
print(f"  class/common.py: {out}")

# 3. Check the pyc file in __pycache__
out, err, code = run(client, "sudo ls -la /www/server/panel/class/__pycache__/common.cpython* 2>&1")
print(f"  Compiled: {out}")

# 4. Read the first few lines if it exists
if "No such file" not in out:
    out2, err, code = run(client, "sudo head -30 /www/server/panel/class/common.py 2>&1")
    print(f"\n  Head:\n{out2}")
    
    out2, err, code = run(client, "sudo wc -l /www/server/panel/class/common.py 2>&1")
    print(f"  Lines: {out2}")
    
    # Check for panelSetup class
    out2, err, code = run(client, "sudo grep -n 'class panelSetup' /www/server/panel/class/common.py 2>&1")
    print(f"  panelSetup class: {out2}")
else:
    print("\n  common.py DOES NOT EXIST in class/ either!")
    
    # Check what's in the __pycache__
    out, err, code = run(client, "sudo ls -la /www/server/panel/class/__pycache__/ 2>&1 | head -20")
    print(f"  __pycache__ contents: {out}")
    
    # Check if pyc can give us info
    out, err, code = run(client, "sudo python3 -c \"import dis, marshal, time; f=open('/www/server/panel/class/__pycache__/common.cpython-312.pyc','rb'); f.read(16); code=marshal.load(f); print('Constants:', [c for c in code.co_consts if isinstance(c, str)][:20])\" 2>&1")
    print(f"  pyc info: {out[:500]}")

# 5. Try downloading from aaPanel's actual GitHub repo structure
print("\n[5] Try downloading from correct GitHub path...")
out, err, code = run(client, "sudo curl -sI 'https://raw.githubusercontent.com/aaPanel/aaPanel/main/class/common.py' 2>&1 | head -5")
print(f"  GitHub class/common.py: {out}")

# If that doesn't work, try different paths
paths_to_try = [
    "https://raw.githubusercontent.com/aaPanel/aaPanel/refs/heads/master/class/common.py",
    "https://raw.githubusercontent.com/aaPanel/aaPanel/develop/class/common.py",
]
for path in paths_to_try:
    out, err, code = run(client, f"sudo curl -sI '{path}' 2>&1 | head -3")
    status = out.split('\n')[0] if out else 'empty'
    print(f"  {path.split('/')[-1]}: {status}")
    if "200" in status:
        print(f"  FOUND! Downloading...")
        out2, err, code = run(client, f"sudo curl -sL '{path}' -o /tmp/common_panel.py 2>&1")
        out2, err, code = run(client, "sudo wc -l /tmp/common_panel.py 2>&1")
        print(f"  Downloaded lines: {out2}")
        out2, err, code = run(client, "sudo head -5 /tmp/common_panel.py 2>&1")
        print(f"  Head: {out2}")
        break

# 6. Try the pip approach with panel's own python
print("\n[6] Try bt update mechanism...")
out, err, code = run(client, "sudo /www/server/panel/pyenv/bin/python3 -c \"import sys; sys.path.insert(0, '/www/server/panel'); import common; print(common.__file__)\" 2>&1")
print(f"  Import test: {out}")

# 7. Try pip list in panel's pyenv
print("\n[7] Panel pyenv packages...")
out, err, code = run(client, "sudo /www/server/panel/pyenv/bin/pip3 list 2>&1 | grep -i panel | head -5")
print(f"  {out}")

client.close()
