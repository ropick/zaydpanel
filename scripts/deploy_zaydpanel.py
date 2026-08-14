#!/usr/bin/env python3
"""Deploy ZaydPanel v3.0 to Oracle ARM VPS."""
import paramiko, sys, os, time, tarfile, io

VPS_IP = "168.110.210.148"
VPS_USER = "opc"
KEY_PATH = "/home/z/my-project/.ssh/oci_key"
PANEL_DIR = "/home/z/zaydpanel/panel"
AGENT_SRC = "/home/z/zaydpanel/agent/zaydpanel-agent.py"
REMOTE_BASE = "/opt/zaydpanel"
PANEL_REMOTE = f"{REMOTE_BASE}/panel"
AGENT_REMOTE = f"{REMOTE_BASE}/agent/zaydpanel-agent.py"

G = '\033[92m'; Y = '\033[93m'; R = '\033[91m'; B = '\033[94m'; NC = '\033[0m'

def log(msg, color=NC): print(f"{color}{msg}{NC}", flush=True)

def ssh_run(client, cmd, timeout=120, sudo=False):
    if sudo: cmd = f"sudo bash -c '{cmd}'"
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    rc = stdout.channel.recv_exit_status()
    return out, err, rc

def main():
    log(f"=== ZaydPanel v3.0 Deploy ===", B)
    
    # SSH Connection
    log("Connecting to VPS...", Y)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.Ed25519Key.from_private_key_file(KEY_PATH)
    client.connect(VPS_IP, username=VPS_USER, pkey=key)
    log(f"Connected to {VPS_IP}", G)
    
    # Prepare remote directories
    log("Preparing remote directories...", Y)
    ssh_run(client, f"mkdir -p {REMOTE_BASE}/panel {REMOTE_BASE}/agent {REMOTE_BASE}/data {REMOTE_BASE}/backups {REMOTE_BASE}/cron", sudo=True)
    
    # Deploy Panel (tar standalone + static)
    log("Packaging panel...", Y)
    panel_tardir = "/tmp/zaydpanel-deploy"
    os.makedirs(panel_tardir, exist_ok=True)
    
    # Copy standalone build
    standalone_src = os.path.join(PANEL_DIR, ".next/standalone")
    static_src = os.path.join(PANEL_DIR, ".next/static")
    public_src = os.path.join(PANEL_DIR, "public")
    
    if not os.path.exists(standalone_src):
        log(f"ERROR: Standalone build not found at {standalone_src}. Run 'npm run build' first.", R)
        sys.exit(1)
    
    # Create tarball in memory
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        def add_dir(base, arcname):
            if not os.path.exists(base): return
            for root, dirs, files in os.walk(base):
                for f in files:
                    full = os.path.join(root, f)
                    arc = os.path.join(arcname, os.path.relpath(full, base))
                    tar.add(full, arcname=arc)
        
        add_dir(standalone_src, "panel/")
        add_dir(static_src, "panel/.next/static/")
        if os.path.exists(public_src):
            add_dir(public_src, "panel/public/")
    
    tar_buffer.seek(0)
    log(f"Panel tarball: {len(tar_buffer.getvalue()) / 1024 / 1024:.1f} MB", Y)
    
    # Upload panel via SFTP
    log("Uploading panel to server...", Y)
    sftp = client.open_sftp()
    
    # Write tarball to remote
    remote_tar = "/tmp/zaydpanel-panel.tar.gz"
    sftp.putfo(tar_buffer, remote_tar)
    log("Panel uploaded.", G)
    
    # Extract on server
    log("Extracting panel on server...", Y)
    ssh_run(client, f"rm -rf {PANEL_REMOTE}/*", sudo=True)
    ssh_run(client, f"tar -xzf {remote_tar} -C {REMOTE_BASE}/", sudo=True)
    ssh_run(client, f"rm -f {remote_tar}", sudo=True)
    log("Panel extracted.", G)
    
    # Deploy Agent
    log("Uploading agent...", Y)
    sftp.put(AGENT_SRC, f"/tmp/zaydpanel-agent.py")
    ssh_run(client, f"cp /tmp/zaydpanel-agent.py {AGENT_REMOTE} && chmod +x {AGENT_REMOTE}", sudo=True)
    ssh_run(client, f"rm -f /tmp/zaydpanel-agent.py", sudo=True)
    log("Agent uploaded.", G)
    
    sftp.close()
    
    # Create systemd services if not exist
    log("Setting up systemd services...", Y)
    
    panel_service = f"""[Unit]
Description=ZaydPanel Web Panel
After=network.target

[Service]
Type=simple
WorkingDirectory={PANEL_REMOTE}
ExecStart=/usr/bin/node {PANEL_REMOTE}/server.js
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=PORT=2080
Environment=AGENT_URL=http://127.0.0.1:8442
Environment=AGENT_SECRET=zc-agent-2026-secret

[Install]
WantedBy=multi-user.target"""
    
    agent_service = f"""[Unit]
Description=ZaydPanel Agent
After=network.target

[Service]
Type=simple
WorkingDirectory={REMOTE_BASE}/agent
ExecStart=/usr/bin/python3 {AGENT_REMOTE}
Restart=always
RestartSec=5
Environment=ZAYDPANEL_AGENT_PORT=8442
Environment=ZAYDPANEL_AGENT_SECRET=zc-agent-2026-secret
Environment=ZAYDPANEL_JWT_SECRET=zc-jwt-2026-super-secret-key

[Install]
WantedBy=multi-user.target"""
    
    # Write service files
    for name, content in [("zaydpanel-panel", panel_service), ("zaydpanel-agent", agent_service)]:
        ssh_run(client, f"cat > /etc/systemd/system/{name}.service << 'SERVICEEOF'\n{content}\nSERVICEEOF", sudo=True)
        ssh_run(client, f"systemctl daemon-reload", sudo=True)
        ssh_run(client, f"systemctl enable {name}", sudo=True)
        ssh_run(client, f"systemctl restart {name}", sudo=True)
        out, err, rc = ssh_run(client, f"systemctl is-active {name}")
        status = G + "RUNNING" + NC if out.strip() == "active" else R + "FAILED" + NC
        log(f"  {name}: {status}")
    
    # Verify
    log("\nVerifying deployment...", Y)
    out, _, rc = ssh_run(client, "curl -s http://127.0.0.1:8442/health")
    log(f"  Agent health: {out}", G if '"ok"' in out else R)
    
    time.sleep(2)
    out, _, rc = ssh_run(client, "curl -s http://127.0.0.1:2080/login -o /dev/null -w '%{http_code}'")
    log(f"  Panel HTTP: {out}", G if "200" in out else R)
    
    client.close()
    log("\n=== Deploy Complete! ===", G)

if __name__ == "__main__":
    main()
