#!/usr/bin/env python3
"""Check panelSetup().init() - likely returning error causing login crash"""
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

# 1. Find panelSetup class and init method
print("[1] Find panelSetup class...")
out, err, code = run(client, "sudo grep -n 'class panelSetup' /www/server/panel/BTPanel/common.py 2>/dev/null")
print(f"  {out}")

# 2. Read init method
if out:
    line = out.split(':')[0].strip()
    # Search for def init within panelSetup
    out2, err, code = run(client, f"sudo grep -n 'def init' /www/server/panel/BTPanel/common.py 2>/dev/null")
    print(f"\n  def init lines: {out2}")
    
    for init_line in out2.split('\n'):
        ln = init_line.split(':')[0].strip()
        if ln:
            out3, _, _ = run(client, f"sudo sed -n '{ln},{int(ln)+60}p' /www/server/panel/BTPanel/common.py 2>/dev/null")
            if 'panelSetup' in out3 or 'self' in out3:
                print(f"\n  --- init at line {ln} ---")
                print(out3[:2000])
                break

# 3. More targeted - find panelSetup init 
print("\n[2] Search panelSetup init directly...")
out, err, code = run(client, "sudo awk '/class panelSetup/,/^class / {print NR\": \"\$0}' /www/server/panel/BTPanel/common.py 2>/dev/null | grep 'def init' | head -5")
print(f"  {out}")

# 4. Just read a big chunk around the panelSetup class
out, err, code = run(client, "sudo grep -n 'class panelSetup' /www/server/panel/BTPanel/common.py 2>/dev/null")
if out:
    start_line = int(out.split(':')[0])
    out2, err, code = run(client, f"sudo sed -n '{start_line},{start_line+200}p' /www/server/panel/BTPanel/common.py 2>/dev/null")
    # Find def init
    for line_item in out2.split('\n'):
        if 'def init' in line_item:
            print(f"\n[3] Found init at: {line_item}")
            break
    print(f"\n  panelSetup class:\n{out2[:3000]}")

client.close()
