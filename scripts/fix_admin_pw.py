#!/usr/bin/env python3
"""Fix admin password in ZaydPanel SQLite DB."""
import paramiko, hashlib

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file("/home/z/my-project/.ssh/oci_key")
client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)

def run(cmd, sudo=False):
    if sudo: cmd = f"sudo bash -c '{cmd}'"
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err

salt = "zaydpanel-salt-2026"
expected = hashlib.sha256(f"{salt}:zaydpanel2026".encode()).hexdigest()

# Get current hash
out, _ = run("sqlite3 /opt/zaydpanel/data/zaydpanel.db \"SELECT password_hash FROM users WHERE username='admin';\"", sudo=True)
print(f"Current DB hash: {out}")
print(f"Expected hash:   {expected}")
print(f"Match: {out == expected}")

if out != expected:
    _, err = run(f"sqlite3 /opt/zaydpanel/data/zaydpanel.db \"UPDATE users SET password_hash='{expected}' WHERE username='admin';\"", sudo=True)
    print(f"Update error: {err}" if err else "Password updated!")
    
    out2, _ = run("sqlite3 /opt/zaydpanel/data/zaydpanel.db \"SELECT password_hash FROM users WHERE username='admin';\"", sudo=True)
    print(f"Verify: {out2 == expected}")

client.close()
print("Done.")
