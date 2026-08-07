#!/usr/bin/env python3
"""Get aaPanel password from database"""
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

# Run from panel directory where public module is accessible
cmds = [
    "cd /www/server/panel && sudo /www/server/panel/pyenv/bin/python3 -c \"import sys; sys.path.insert(0,'class/'); sys.path.insert(0,'.'); import public; info = public.M('users').where(id=1).field('username,password,email').select(); print(info)\" 2>&1",
    # Try sqlite directly
    "sudo sqlite3 /www/server/panel/data/default.db 'SELECT username, password FROM users LIMIT 1;' 2>&1",
    "sudo ls /www/server/panel/data/*.db 2>&1",
]

for cmd in cmds:
    out, err, code = run(client, cmd)
    print(f"[{cmd[:60]}...]")
    print(f"  out: {out[:500]}")
    print(f"  err: {err[:200]}")
    print()

client.close()
