#!/usr/bin/env python3
"""Check aaPanel installation progress and status"""
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
    code = stdout.channel.recv_exit_status()
    return out, code

client = connect()

# Check if install is still running
out, _ = run(client, "ps aux | grep 'install_6.0' | grep -v grep")
print(f"Install process running: {'YES' if out else 'NO'}")

# Check install log
out, _ = run(client, "tail -30 /tmp/aapanel_install.log 2>/dev/null")
print(f"\nLast 30 lines of install log:\n{out}")

# Check exit code
out, _ = run(client, "grep 'INSTALL_EXIT_CODE' /tmp/aapanel_install.log 2>/dev/null")
print(f"\nExit code marker: {out}")

# Check if bt command exists
out, _ = run(client, "which bt 2>/dev/null")
print(f"\nbt command: {out if out else 'NOT FOUND'}")

# Check panel info
out, _ = run(client, "bt default 2>/dev/null")
print(f"\nbt default: {out if out else 'N/A'}")

# Port check
out, _ = run(client, "ss -tlnp | grep -E ':(80|443|8888|3306) '")
print(f"\nPorts: {out if out else 'None'}")

# Docker check
out, _ = run(client, "docker ps --format '{{.Names}} {{.Status}}'")
print(f"\nDocker: {out if out else 'No containers'}")

client.close()
