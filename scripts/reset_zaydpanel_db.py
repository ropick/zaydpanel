#!/usr/bin/env python3
"""Reset ZaydPanel DB and restart agent to reinitialize."""
import paramiko, time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file("/home/z/my-project/.ssh/oci_key")
client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)

def run(cmd, sudo=False, timeout=15):
    if sudo: cmd = f"sudo bash -c '{cmd}'"
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err

# Stop agent
print("Stopping agent...")
out, err = run("systemctl stop zaydpanel-agent", sudo=True, timeout=30)
print(f"  Stop: err={err if err else 'none'}")

# Backup old DB
print("Backing up old DB...")
out, err = run("cp /opt/zaydpanel/data/zaydpanel.db /opt/zaydpanel/data/zaydpanel.db.bak 2>/dev/null; echo ok", sudo=True)
print(f"  Backup: {out}")

# Delete old DB
print("Deleting old DB...")
out, err = run("rm -f /opt/zaydpanel/data/zaydpanel.db", sudo=True)
print(f"  Delete: err={err if err else 'none'}")

# Start agent (will reinit DB with correct schema)
print("Starting agent...")
out, err = run("systemctl start zaydpanel-agent", sudo=True, timeout=15)
print(f"  Start: err={err if err else 'none'}")

time.sleep(3)

# Verify
print("Verifying...")
out, err = run("curl -s http://127.0.0.1:8442/health", timeout=10)
print(f"  Health: {out}")

out, err = run("curl -s -X POST http://127.0.0.1:8442/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"zaydpanel2026\"}'", timeout=10)
print(f"  Login: {out[:300]}")

# Check DB
out, err = run("sqlite3 /opt/zaydpanel/data/zaydpanel.db 'SELECT id,username,role,status FROM users;'", sudo=True, timeout=10)
print(f"  Users: {out}")

out, err = run("sqlite3 /opt/zaydpanel/data/zaydpanel.db 'SELECT id,name,slug FROM packages;'", sudo=True, timeout=10)
print(f"  Packages: {out}")

client.close()
print("Done.")
