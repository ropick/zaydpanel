#!/usr/bin/env python3
"""Diagnose: Check panel.sock and Python app status"""
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

print("=" * 60)
print("DIAGNOSE: panel.sock + Python app status")
print("=" * 60)

# 1. Check if panel.sock exists
print("\n[1] Check panel.sock...")
out, err, code = run(client, "sudo ls -la /tmp/panel.sock 2>&1")
print(f"  panel.sock: {out if out else 'NOT FOUND'}")

# 2. Check what's in /tmp related to panel
print("\n[2] Panel-related files in /tmp...")
out, err, code = run(client, "sudo ls -la /tmp/ | grep -i panel 2>&1")
print(f"  {out if out else 'none'}")

# 3. Check all socket files
print("\n[3] All socket files in /tmp...")
out, err, code = run(client, "sudo find /tmp -name '*.sock' -o -name '*.socket' 2>/dev/null")
print(f"  Sockets: {out if out else 'none'}")

# 4. Check BT-Panel process and its args
print("\n[4] BT-Panel process...")
out, err, code = run(client, "ps aux | grep BT-Panel | grep -v grep")
print(f"  Process: {out if out else 'NOT RUNNING'}")

# 5. Check webserver process
print("\n[5] Webserver process...")
out, err, code = run(client, "ps aux | grep webserver | grep -v grep")
print(f"  Process: {out if out else 'NOT RUNNING'}")

# 6. Check webserver error log
print("\n[6] Webserver error log...")
out, err, code = run(client, "sudo cat /www/server/panel/webserver/logs/error.log 2>&1")
print(f"  Error: {out[:500] if out else 'N/A'}")

print("\n[7] Webserver access/error log...")
out, err, code = run(client, "sudo cat /www/server/panel/webserver/logs/webserver.log 2>&1")
print(f"  Webserver log: {out[:500] if out else 'N/A'}")

# 8. Check if webserver is running on port 36977
print("\n[8] Port 36977 status...")
out, err, code = run(client, "sudo ss -tlnp | grep 36977")
print(f"  Port: {out if out else 'NOT LISTENING'}")

# 9. Check BT-Panel output/log
print("\n[9] BT-Panel startup - check for errors...")
# Run BT-Panel manually to see output
out, err, code = run(client, "sudo /www/server/panel/pyenv/bin/python3 /www/server/panel/BT-Panel --help 2>&1 | head -10")
print(f"  Help: {out[:300]}")

# 10. Try running panel and see what happens (brief test)
print("\n[10] Check panel run script...")
out, err, code = run(client, "sudo cat /www/server/panel/script/webserver-ctl.sh 2>&1")
print(f"  Control script:\n{out}")

# 11: Check if panel.py has a startup log
print("\n[11] Panel runtime logs...")
out, err, code = run(client, "sudo ls -la /www/server/panel/logs/ 2>&1")
print(f"  Log files: {out}")

for logfile in ['error.log', 'request.log', 'panel.log']:
    out, err, code = run(client, f"sudo tail -10 /www/server/panel/logs/{logfile} 2>&1")
    if out:
        print(f"  {logfile}: {out[:300]}")

# 12: Restart and immediately check
print("\n[12] Fresh restart with monitoring...")
out, err, code = run(client, "sudo bt stop 2>&1")
print(f"  Stop: {out if out else 'done'}")
time.sleep(1)

# Start in background and check
out, err, code = run(client, "nohup sudo /www/server/panel/pyenv/bin/python3 /www/server/panel/BT-Panel > /tmp/panel_output.log 2>&1 &")
time.sleep(3)

# Check if socket appeared
out, err, code = run(client, "sudo ls -la /tmp/panel.sock 2>&1")
print(f"  panel.sock after start: {out if out else 'NOT FOUND'}")

# Check startup log
out, err, code = run(client, "sudo cat /tmp/panel_output.log 2>&1")
print(f"  Panel output: {out[:500] if out else 'empty'}")

# Check webserver too
out, err, code = run(client, "sudo /www/server/panel/pyenv/bin/python3 /www/server/panel/BT-Task > /tmp/task_output.log 2>&1 &")
time.sleep(2)

# Now check webserver
out, err, code = run(client, "sudo /www/server/panel/webserver/sbin/webserver -t -c /www/server/panel/webserver/conf/webserver.conf 2>&1")
print(f"  Webserver config test: {out[:300]}")

# Start webserver manually
out, err, code = run(client, "nohup sudo /www/server/panel/webserver/sbin/webserver -c /www/server/panel/webserver/conf/webserver.conf > /tmp/webserver_output.log 2>&1 &")
time.sleep(2)

# Check
out, err, code = run(client, "sudo cat /tmp/webserver_output.log 2>&1")
print(f"  Webserver output: {out[:300]}")

out, err, code = run(client, "sudo ss -tlnp | grep 36977")
print(f"  Port 36977: {out if out else 'NOT LISTENING'}")

# Test
out, err, code = run(client, "curl -sI http://127.0.0.1:36977/ --connect-timeout 5 2>&1")
print(f"  curl test: {out[:400]}")

client.close()
print("\n" + "=" * 60)
