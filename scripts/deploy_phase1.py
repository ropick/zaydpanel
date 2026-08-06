import paramiko
import sys
import os
import time

VPS_IP = "168.110.210.148"
VPS_USER = "opc"
KEY_PATH = "/home/z/my-project/deploy/nusahost_id"
REMOTE_DIR = "/opt/nusahost"
TARBALL = "/tmp/nusahost-deploy.tar.gz"

def connect():
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(VPS_IP, username=VPS_USER, pkey=key, timeout=15)
    return client

def run(client, cmd, timeout=300):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

def stream(client, cmd, timeout=600):
    channel = client.get_transport().open_session()
    channel.settimeout(timeout)
    channel.get_pty()
    channel.exec_command(cmd)
    output = ""
    while True:
        if channel.recv_ready():
            d = channel.recv(4096).decode(); output += d; print(d, end='', flush=True)
        if channel.recv_stderr_ready():
            d = channel.recv_stderr(4096).decode(); output += d; print(d, end='', flush=True)
        if channel.exit_status_ready():
            while channel.recv_ready(): output += channel.recv(4096).decode()
            break
        time.sleep(0.1)
    return output, channel.recv_exit_status()

def upload(client, local, remote):
    sftp = client.open_sftp()
    rdir = os.path.dirname(remote)
    try: sftp.stat(rdir)
    except: 
        for p in rdir.split('/'):
            if not p: continue
            # simplified mkdir
            pass
    sftp.put(local, remote)
    sftp.close()

client = connect()
print("SSH Connected\n")

# Step 1: Prepare dir
print("[1/4] Prepare directory...")
run(client, f"sudo mkdir -p {REMOTE_DIR} && sudo chown -R opc:opc {REMOTE_DIR}")
print("  Done\n")

# Step 2: Upload
print("[2/4] Upload project...")
os.system(f"cd /home/z/my-project && tar czf {TARBALL} --exclude='node_modules' --exclude='.next' --exclude='db' --exclude='__debugger' --exclude='.git' --exclude='*.log' --exclude='tests' --exclude='examples' --exclude='worklog.md' src/ public/ prisma/ package.json bun.lock next.config.ts tailwind.config.ts postcss.config.mjs tsconfig.json components.json eslint.config.mjs deploy/ .env")
size = os.path.getsize(TARBALL)
print(f"  Package: {size/1024:.0f} KB")

sftp = client.open_sftp()
sftp.put(TARBALL, f"{REMOTE_DIR}/nusahost.tar.gz")
sftp.close()
print("  Uploaded\n")

# Step 3: Extract
print("[3/4] Extract...")
out, err, code = run(client, f"cd {REMOTE_DIR} && tar xzf nusahost.tar.gz && rm nusahost.tar.gz && ls")
print(f"  {out}\n")

# Step 4: Install Docker
print("[4/4] Install Docker & start...")
out, err, code = run(client, "docker --version 2>/dev/null")
if code == 0:
    print(f"  Docker already: {out}")
else:
    print("  Installing Docker...")
    out, ec = stream(client, """
sudo dnf install -y dnf-utils
sudo dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker opc
docker --version
""", timeout=300)
print(f"  Exit: {ec}\n")

client.close()
print("\nPHASE 1 DONE - Files uploaded, Docker ready")
