import paramiko, time

def connect():
    key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect('168.110.210.148', username='opc', pkey=key, timeout=15)
    return c

def run(c, cmd, timeout=60):
    stdin, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    code = stdout.channel.recv_exit_status()
    return out, err, code

def stream(c, cmd, timeout=300):
    channel = c.get_transport().open_session()
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

c = connect()
print("=" * 50)
print("  FASE 1: Open Ports (iptables)")
print("=" * 50)

ports = [
    ("2222", "DirectAdmin"),
    ("20", "FTP Active"),
    ("21", "FTP"),
    ("49152-65535", "FTP Passive"),
]

for port, desc in ports:
    out, err, code = run(c, f"sudo iptables -C INPUT -m state --state NEW -p tcp --dport {port} -j ACCEPT 2>/dev/null && echo EXISTS || sudo iptables -I INPUT -m state --state NEW -p tcp --dport {port} -j ACCEPT && echo ADDED")
    print(f"  Port {port:15s} ({desc:15s}) => {out.strip()}")

# Save
run(c, "sudo sh -c 'iptables-save > /etc/iptables.rules'")
print("  Rules saved to /etc/iptables.rules\n")

print("=" * 50)
print("  FASE 2.1: Update OS & Install Utils")
print("=" * 50)
out, code = stream(c, "sudo dnf update -y 2>&1 | tail -20", timeout=120)
print(f"\n  Exit code: {code}\n")

print("=" * 50)
print("  FASE 2.1b: Install utilities")
print("=" * 50)
out, code = stream(c, "sudo dnf install -y wget curl nano perl tar 2>&1 | tail -10", timeout=120)
print(f"\n  Exit code: {code}\n")

print("=" * 50)
print("  FASE 2.2: Create Swap (4GB)")
print("=" * 50)

# Check existing swap
out, _, _ = run(c, "swapon --show")
if out.strip():
    print(f"  Swap already exists: {out}")
else:
    print("  Creating 4GB swap file...")
    out, code = stream(c, """
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
echo "SWAP CREATED"
""", timeout=60)
    
# Verify
out, _, _ = run(c, "free -h | grep Swap")
print(f"  Swap status: {out}")

print("\n" + "=" * 50)
print("  FASE 2.3: Firewall (firewalld)")
print("=" * 50)
fw_ports = [2222, 20, 21]
for port in fw_ports:
    run(c, f"sudo firewall-cmd --permanent --add-port={port}/tcp 2>/dev/null")
print(f"  Ports {fw_ports} added to firewalld")

# FTP passive range
out, _, _ = run(c, "sudo firewall-cmd --permanent --add-port=49152-65535/tcp 2>/dev/null")
print(f"  FTP Passive (49152-65535): {'OK' if not out else out}")

run(c, "sudo firewall-cmd --reload 2>/dev/null")
print("  Firewalld reloaded\n")

print("=" * 50)
print("  FASE 2.4: Set Hostname")
print("=" * 50)
out, _, _ = run(c, "hostnamectl")
print(f"  Current: {out.strip()}")

# Set hostname - user needs ns1/ns2 subdomain
out, err, code = run(c, "sudo hostnamectl set-hostname host.pro99.my.id 2>&1")
print(f"  Set to: host.pro99.my.id => {'OK' if code == 0 else err}")

out, _, _ = run(c, "hostname")
print(f"  Verified: {out.strip()}")

# Also add to /etc/hosts
run(c, "sudo sh -c 'echo \"168.110.210.148 host.pro99.my.id\" >> /etc/hosts'")
print("  Added to /etc/hosts\n")

# Final summary
print("=" * 50)
print("  SUMMARY")
print("=" * 50)
out, _, _ = run(c, "free -h")
print(out)
out, _, _ = run(c, "df -h / | tail -1")
print(f"Disk: {out}")
out, _, _ = run(c, "sudo iptables -L INPUT -n | grep -c ACCEPT")
print(f"Open firewall rules: {out}")
out, _, _ = run(c, "uptime")
print(f"Uptime: {out}")

print("\nFASE 1 & 2 COMPLETE!")
print("\nNEXT: FASE 3 - Install DirectAdmin")
print("  PREREQUISITE: Anda harus beli lisensi DirectAdmin dulu")
print("  URL: https://www.directadmin.com/pricing/")
print("  Setelah dapat Client ID + License ID, lanjut ke FASE 3")

c.close()
