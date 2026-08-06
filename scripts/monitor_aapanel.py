#!/usr/bin/env python3
"""Monitor aaPanel installation progress"""
import paramiko, time, sys

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

for i in range(40):  # Check every 30s, up to 20 min
    time.sleep(30)
    
    # Check processes
    procs, _ = run(client, "ps aux | grep -E 'install_6|aapanel' | grep -v grep")
    
    # Check log
    log, _ = run(client, "tail -5 /tmp/aapanel_install.log 2>/dev/null")
    
    # Check if bt exists
    bt, _ = run(client, "sudo which bt 2>/dev/null")
    
    elapsed = (i + 1) * 30
    mins = elapsed // 60
    secs = elapsed % 60
    
    status = "🔄 RUNNING" if procs else "🏁 ENDED"
    print(f"[{mins:02d}:{secs:02d}] {status}")
    if log:
        for line in log.split('\n')[-3:]:
            c = line.strip()[:130]
            if c:
                print(f"  {c}")
    
    if bt:
        print(f"\n🎉 aaPanel installed! bt found at: {bt}")
        time.sleep(5)
        
        # Get credentials
        out, _ = run(client, "sudo bt default 2>/dev/null")
        if out:
            print(f"\n─── Panel Credentials ───")
            for line in out.split('\n'):
                print(f"  {line}")
        
        # Get panel URL from log
        log_full, _ = run(client, "cat /tmp/aapanel_install.log 2>/dev/null")
        for line in log_full.split('\n'):
            if any(k in line.lower() for k in ['congratulat', 'panel', 'url', 'username', 'password', 'http://', 'https://']):
                print(f"  {line.strip()}")
        
        # Check ports
        ports, _ = run(client, "ss -tlnp 2>/dev/null | grep -E ':(80|443|8888|3306) '")
        print(f"\nPorts:\n{ports}" if ports else "Ports: checking...")
        
        # Panel health
        out2, _ = run(client, "curl -sI http://localhost:8888 2>/dev/null | head -3")
        print(f"Panel (8888): {out2.strip() if out2 else 'N/A'}")
        
        # Docker app
        docker, _ = run(client, "docker ps --format '{{.Names}} {{.Status}}' 2>/dev/null")
        print(f"Docker: {docker}")
        
        app, _ = run(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null")
        print(f"Next.js (3000): HTTP {app}")
        
        break
    
    if not procs:
        print("\n⚠️ Process ended but bt not found. Checking full log tail...")
        full_log, _ = run(client, "tail -50 /tmp/aapanel_install.log 2>/dev/null")
        print(full_log)
        
        # Maybe it installed but as a different command
        out2, _ = run(client, "ls /www/server/panel/ 2>/dev/null")
        if out2:
            print(f"\n⚠️ Panel dir exists but bt not in PATH. {out2[:100]}")
        
        break

client.close()
