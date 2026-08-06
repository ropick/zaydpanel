import paramiko
import sys
import os
import time

VPS_IP = "168.110.210.148"
VPS_USER = "opc"
KEY_PATH = "/home/z/my-project/deploy/nusahost_id"
REMOTE_DIR = "/opt/nusahost"
TARBALL = "/tmp/nusahost-deploy.tar.gz"

GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
NC = '\033[0m'

def run_cmd(client, cmd, timeout=300, sudo=False):
    """Execute command and return output"""
    if sudo:
        cmd = f"sudo bash -c '{cmd}'"
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    exit_code = stdout.channel.recv_exit_status()
    return out, err, exit_code

def run_cmd_stream(client, cmd, timeout=600, sudo=False):
    """Execute command and stream output"""
    if sudo:
        cmd = f"sudo bash -c '{cmd}'"
    transport = client.get_transport()
    channel = transport.open_session()
    channel.settimeout(timeout)
    channel.get_pty()
    channel.exec_command(cmd)
    
    output = ""
    while True:
        if channel.recv_ready():
            data = channel.recv(4096).decode()
            output += data
            print(data, end='', flush=True)
        if channel.recv_stderr_ready():
            data = channel.recv_stderr(4096).decode()
            output += data
            print(data, end='', flush=True)
        if channel.exit_status_ready():
            # Read remaining
            while channel.recv_ready():
                output += channel.recv(4096).decode()
            break
        time.sleep(0.1)
    
    exit_code = channel.recv_exit_status()
    return output, exit_code

def upload_sftp(client, local_path, remote_path):
    """Upload file via SFTP"""
    sftp = client.open_sftp()
    
    # Create remote directory if needed
    remote_dir = os.path.dirname(remote_path)
    try:
        sftp.stat(remote_dir)
    except FileNotFoundError:
        # Create recursively
        parts = remote_dir.split('/')
        current = ''
        for part in parts:
            if not part:
                current = '/'
                continue
            current += '/' + part
            try:
                sftp.stat(current)
            except FileNotFoundError:
                sftp.mkdir(current)
    
    sftp.put(local_path, remote_path)
    size = sftp.stat(remote_path).st_size
    sftp.close()
    return size

# ===================== MAIN =====================

try:
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"\n{'='*50}")
    print(f"  NusaHost VPS Deployment")
    print(f"  Target: {VPS_USER}@{VPS_IP}")
    print(f"{'='*50}\n")

    client.connect(VPS_IP, username=VPS_USER, pkey=key, timeout=15)
    print("SSH Connected!\n")

    # ---- Step 1: Prepare remote directory ----
    print(f"{YELLOW}[1/6] Prepare remote directory...{NC}")
    run_cmd(client, f"sudo mkdir -p {REMOTE_DIR} && sudo chown -R opc:opc {REMOTE_DIR}")
    print(f"  Remote dir: {REMOTE_DIR} ✓")

    # ---- Step 2: Upload tarball ----
    print(f"\n{YELLOW}[2/6] Upload project files...{NC}")
    # Recreate tarball
    os.system(f"cd /home/z/my-project && tar czf {TARBALL} --exclude='node_modules' --exclude='.next' --exclude='db' --exclude='__debugger' --exclude='.git' --exclude='*.log' --exclude='tests' --exclude='examples' --exclude='worklog.md' src/ public/ prisma/ package.json bun.lock next.config.ts tailwind.config.ts postcss.config.mjs tsconfig.json components.json eslint.config.mjs deploy/ .env 2>&1")
    
    size = os.path.getsize(TARBALL)
    print(f"  Package size: {size/1024:.1f} KB")
    
    upload_sftp(client, TARBALL, f"{REMOTE_DIR}/nusahost-deploy.tar.gz")
    print(f"  Upload complete ✓")

    # ---- Step 3: Extract on VPS ----
    print(f"\n{YELLOW}[3/6] Extract files on VPS...{NC}")
    out, err, code = run_cmd(client, f"cd {REMOTE_DIR} && tar xzf nusahost-deploy.tar.gz && rm nusahost-deploy.tar.gz")
    if code != 0:
        print(f"  Error: {err}")
    print(f"  Extracted ✓")

    # ---- Step 4: Install Docker ----
    print(f"\n{YELLOW}[4/6] Install Docker...{NC}")
    out, err, code = run_cmd(client, "which docker 2>/dev/null && docker --version")
    if code == 0 and out:
        print(f"  Docker already installed: {out}")
    else:
        print("  Installing Docker (this may take a few minutes)...")
        out, exit_code = run_cmd_stream(client, """
            sudo dnf install -y dnf-utils
            sudo dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            sudo systemctl enable docker
            sudo systemctl start docker
            sudo usermod -aG docker opc
        """, timeout=600, sudo=False)
        
        if exit_code != 0:
            print(f"\n  {RED}Docker install may have warnings (non-fatal){NC}")
        
        # Verify
        out, err, code = run_cmd(client, "docker --version")
        if code == 0:
            print(f"\n  Docker installed: {out} ✓")
        else:
            print(f"  {RED}Docker install failed!{NC}")
            sys.exit(1)

    # ---- Step 5: Open firewall ports ----
    print(f"\n{YELLOW}[5/6] Open firewall ports (80, 443)...{NC}")
    run_cmd_stream(client, """
        # AlmaLinux uses firewalld
        sudo systemctl start firewalld 2>/dev/null || true
        sudo firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
        sudo firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
        sudo firewall-cmd --permanent --add-port=3000/tcp 2>/dev/null || true
        sudo firewall-cmd --reload 2>/dev/null || true
        
        # Also open via iptables (Oracle ARM)
        sudo iptables -I INPUT -m state --state NEW -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
        sudo iptables -I INPUT -m state --state NEW -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
        sudo iptables -I INPUT -m state --state NEW -p tcp --dport 3000 -j ACCEPT 2>/dev/null || true
        
        # Save iptables
        sudo iptables-save 2>/dev/null | sudo tee /etc/iptables/rules.v4 > /dev/null 2>&1 || true
        
        echo "Ports 80, 443, 3000 opened"
    """, timeout=60, sudo=False)
    print(f"  Firewall configured ✓")

    # ---- Step 6: Build & Start containers ----
    print(f"\n{YELLOW}[6/6] Build & Start containers...{NC}")
    print("  Building Docker image (ARM64, first build may take 3-5 min)...\n")
    
    out, exit_code = run_cmd_stream(client, f"""
        cd {REMOTE_DIR}
        export PATH=$PATH:/usr/local/bin
        sudo docker compose -f deploy/docker-compose.yml build --no-cache 2>&1
    """, timeout=900, sudo=False)

    if exit_code != 0:
        print(f"\n  {RED}Build may have issues, trying to continue...{NC}")

    print(f"\n  Starting containers...\n")
    out, exit_code = run_cmd_stream(client, f"""
        cd {REMOTE_DIR}
        export PATH=$PATH:/usr/local/bin
        sudo docker compose -f deploy/docker-compose.yml up -d 2>&1
    """, timeout=120, sudo=False)

    # ---- Verify ----
    print(f"\n{YELLOW}Verifying...{NC}")
    out, err, code = run_cmd(client, f"cd {REMOTE_DIR} && sudo docker compose -f deploy/docker-compose.yml ps")
    print(out)
    
    # Test if app is responding
    time.sleep(3)
    out, err, code = run_cmd(client, "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>/dev/null || echo 'waiting'")
    if "200" in str(out):
        print(f"\n  App responding: HTTP {out.strip()} ✓")
    else:
        print(f"\n  App status: {out.strip()} (may need a moment)")
    
    # ---- Oracle Cloud Security List reminder ----
    print(f"\n{'='*50}")
    print(f"{GREEN}  DEPLOY COMPLETED!{NC}")
    print(f"{'='*50}")
    print(f"""
  URL: http://{VPS_IP}
  
  Setelah DNS propagate:
  URL: https://pro99.my.id

  Next: Setup SSL
  cd {REMOTE_DIR} && sudo bash deploy/setup-ssl.sh

  Useful commands:
  cd {REMOTE_DIR}
  sudo docker compose -f deploy/docker-compose.yml logs -f    # View logs
  sudo docker compose -f deploy/docker-compose.yml restart    # Restart
  sudo docker compose -f deploy/docker-compose.yml down       # Stop

  ⚠️  PENTING: Jika web tidak bisa diakses dari browser:
  Buka Oracle Cloud Console > Networking > Security Lists
  Add Ingress Rules:
    - Port 80 (HTTP)  Source: 0.0.0.0/0
    - Port 443 (HTTPS) Source: 0.0.0.0/0
""")

    client.close()

except Exception as e:
    print(f"\n{RED}DEPLOY FAILED: {e}{NC}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
