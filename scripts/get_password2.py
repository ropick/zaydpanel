#!/usr/bin/env python3
"""Get aaPanel password - try multiple methods"""
import paramiko

def connect():
    key = paramiko.RSAKey.from_private_key_file("/home/z/my-project/deploy/nusahost_id")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=15):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

client = connect()

# Method 1: Read from panel user database
cmds = [
    "sudo cat /www/server/panel/data/user_info.json 2>/dev/null",
    "sudo /www/server/panel/pyenv/bin/python3 -c \"import sys; sys.path.insert(0,'class/'); import public; print(public.M('users').where(id=1).field('username,password').select())\" 2>/dev/null",
    "sudo bt 14 2>/dev/null",  # bt 14 = change panel password
]

for cmd in cmds:
    out, err, code = run(client, cmd)
    if out and code == 0:
        print(f"Cmd: {cmd.split('|')[0].strip()}")
        print(f"Result: {out[:300]}\n")

# Get password from database directly
out, err, code = run(client, "sudo /www/server/panel/pyenv/bin/python3 -c \"import sys; sys.path.insert(0,'class/'); import public; pwd = public.M('users').where(id=1).getField('password'); print('Hash:', pwd[:30])\" 2>&1")
print(f"Password hash: {out}")

# Try to get the admin_path
out, err, code = run(client, "sudo cat /www/server/panel/data/admin_path.pl 2>&1")
print(f"Admin path: {out}")

client.close()
