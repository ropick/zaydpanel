#!/usr/bin/env python3
"""Check and restore common.py - the core issue"""
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

# 1. Check common.py file size
print("[1] Check common.py...")
out, err, code = run(client, "sudo ls -la /www/server/panel/BTPanel/common.py 2>&1")
print(f"  File: {out}")

out, err, code = run(client, "sudo wc -c /www/server/panel/BTPanel/common.py 2>&1")
print(f"  Bytes: {out}")

out, err, code = run(client, "sudo cat /www/server/panel/BTPanel/common.py 2>&1")
print(f"  Content: '{out}'")

# 2. Check common.pyc
print("\n[2] Check common.pyc...")
out, err, code = run(client, "sudo find /www/server/panel -name 'common.pyc' -o -name 'common.cpython*' 2>/dev/null")
print(f"  Compiled files: {out}")

# 3. Check if there's a backup
print("\n[3] Check for backups...")
out, err, code = run(client, "sudo find /www/server/panel -name 'common.py.bak' -o -name 'common.py.old' 2>/dev/null")
print(f"  Backups: {out}")

# 4. Check git or version control
print("\n[4] Check version/config...")
out, err, code = run(client, "sudo cat /www/server/panel/config/config.json 2>&1")
print(f"  Config: {out}")

# 5. Try to restore common.py from aaPanel update
print("\n[5] Try to restore via aaPanel update...")
# First check what version we have
out, err, code = run(client, "sudo cat /www/server/panel/data/version.pl 2>/dev/null")
print(f"  Version: {out if out else 'NOT FOUND'}")

# Check if there's an update script we can use
out, err, code = run(client, "sudo ls /www/server/panel/update/ 2>/dev/null")
print(f"  Update dir: {out if out else 'NOT FOUND'}")

# Check pyenv for a cached version
out, err, code = run(client, "sudo find /www/server/panel/pyenv -name 'common.py' 2>/dev/null | head -3")
print(f"  In pyenv: {out}")

# 6. Try to download common.py from aaPanel repo
print("\n[6] Download common.py from aaPanel GitHub...")
# aaPanel open source - try to get from GitHub
cmds = [
    # First try the aaPanel official update mechanism
    "sudo /www/server/panel/pyenv/bin/python3 -c 'import panel; print(panel.__file__)' 2>&1",
    # Check if bt has a repair/update option
]
for cmd in cmds:
    out, err, code = run(client, cmd)
    if out:
        print(f"  {out[:200]}")

# 7. Try to get common.py from aaPanel's own update server
print("\n[7] Repair using pip/aaPanel tools...")
out, err, code = run(client, "sudo pip3 install aapanel 2>&1 | tail -5")
print(f"  pip: {out[:300]}")

# 8. Alternative: use curl to download common.py from aaPanel source
print("\n[8] Download common.py from aaPanel GitHub...")
out, err, code = run(client, """
sudo curl -sL "https://raw.githubusercontent.com/aaPanel/aaPanel/refs/heads/main/BTPanel/common.py" -o /tmp/common.py 2>&1
echo "Download code: $?"
sudo wc -l /tmp/common.py 2>&1
""")
print(f"  {out}")

# 9. Check if the download worked
out, err, code = run(client, "sudo head -20 /tmp/common.py 2>&1")
print(f"\n  Downloaded file head:\n{out}")

# If downloaded successfully, copy it
if "class" in out:
    print("\n[9] File looks valid, copying to panel...")
    # Backup the empty one first
    run(client, "sudo cp /www/server/panel/BTPanel/common.py /www/server/panel/BTPanel/common.py.empty_bak")
    run(client, "sudo cp /tmp/common.py /www/server/panel/BTPanel/common.py")
    
    # Clear pyc cache
    run(client, "sudo find /www/server/panel/BTPanel/__pycache__ -name 'common*' -delete 2>&1")
    
    # Restart
    run(client, "sudo bt restart 2>&1")
    time.sleep(5)
    
    # Test
    out, err, code = run(client, "curl -skI 'https://127.0.0.1:36977/613ccb60/' --connect-timeout 5 2>&1")
    print(f"\n  Test after fix: {out[:400]}")
else:
    print("\n[!] Downloaded file is not valid Python. Trying alternative...")
    # Check the raw URL format
    out, err, code = run(client, "sudo curl -sI 'https://raw.githubusercontent.com/aaPanel/aaPanel/main/BTPanel/common.py' 2>&1 | head -5")
    print(f"  GitHub response: {out}")

client.close()
