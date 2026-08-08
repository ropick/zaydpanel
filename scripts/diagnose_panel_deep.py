#!/usr/bin/env python3
"""Deep diagnose: Check why Flask app returns 404 through unix socket"""
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
print("DEEP DIAGNOSE: Flask app 404 through socket")
print("=" * 60)

# 1. Check the full error.log
print("\n[1] Full panel error log...")
out, err, code = run(client, "sudo cat /www/server/panel/logs/error.log 2>&1")
print(f"  Error log:\n{out}")

# 2. Check task.log for errors
print("\n[2] Task log (last 30 lines)...")
out, err, code = run(client, "sudo tail -30 /www/server/panel/logs/task.log 2>&1")
print(f"  Task log:\n{out[:800]}")

# 3. Test directly through unix socket with curl
print("\n[3] Test through unix socket directly...")
out, err, code = run(client, "curl -sI --unix-socket /tmp/panel.sock http://localhost/ --connect-timeout 5 2>&1")
print(f"  Unix socket test: {out[:400]}")
print(f"  Error: {err[:200]}")

# 4. Test with security path through unix socket
print("\n[4] Test security path through unix socket...")
out, err, code = run(client, "curl -sI --unix-socket /tmp/panel.sock http://localhost/613ccb60/ --connect-timeout 5 2>&1")
print(f"  Unix socket + security path: {out[:400]}")

# 5. Get full body response through unix socket
print("\n[5] Full body through unix socket...")
out, err, code = run(client, "curl -s --unix-socket /tmp/panel.sock http://localhost/ --connect-timeout 5 2>&1")
print(f"  Body: {out[:500]}")

# 6. Test through unix socket with longer timeout
print("\n[6] Root path with verbose...")
out, err, code = run(client, "curl -sv --unix-socket /tmp/panel.sock http://localhost/ 2>&1 | head -30")
print(f"  Verbose: {out[:600]}")

# 7. Check the BTPanel routes
print("\n[7] Check Flask routes...")
out, err, code = run(client, "cd /www/server/panel && sudo /www/server/panel/pyenv/bin/python3 -c \"import sys; sys.path.insert(0, '.'); from BTPanel import app; print([r.rule for r in app.url_map.iter_rules()])\" 2>&1")
print(f"  Routes: {out[:500]}")

# 8. Check if panel is in debug mode
print("\n[8] Debug mode check...")
out, err, code = run(client, "sudo test -f /www/server/panel/data/debug.pl && echo 'DEBUG ON' || echo 'DEBUG OFF'")
print(f"  Debug: {out}")

# 9. Try to manually run a test request against Flask
print("\n[9] Direct Flask test...")
out, err, code = run(client, """sudo /www/server/panel/pyenv/bin/python3 -c "
import sys
sys.path.insert(0, '/www/server/panel')
os = __import__('os')
os.chdir('/www/server/panel')
from BTPanel import app
with app.test_client() as c:
    r = c.get('/')
    print(f'Status: {r.status_code}')
    print(f'Headers: {dict(r.headers)}')
    print(f'Body: {r.data[:200]}')
" 2>&1""")
print(f"  Flask test: {out[:500]}")

# 10. Check webserver log after our test
print("\n[10] Webserver log after tests...")
out, err, code = run(client, "sudo cat /www/server/panel/webserver/logs/webserver.log 2>&1")
print(f"  Webserver log: {out[:500] if out else 'empty'}")

# 11: Check if maybe the 404 comes from the proxy (upstream) vs webserver itself
print("\n[11] Detailed curl with headers...")
out, err, code = run(client, "curl -sv http://127.0.0.1:36977/ 2>&1 | head -40")
print(f"  Detailed: {out[:800]}")

client.close()
print("\n" + "=" * 60)
