import paramiko
import sys

VPS_IP = "168.110.210.148"
VPS_USER = "opc"
KEY_PATH = "/home/z/my-project/deploy/nusahost_id"

try:
    # Read key bytes
    with open(KEY_PATH, 'r') as f:
        key_data = f.read()

    # Load as Ed25519 from string
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"Connecting to {VPS_USER}@{VPS_IP}...")
    client.connect(VPS_IP, username=VPS_USER, pkey=key, timeout=15)
    print("CONNECTED OK!\n")

    commands = [
        "whoami",
        "hostname",
        "uname -m",
        "cat /etc/os-release | head -4",
        "df -h / | tail -1",
        "free -h | head -2",
        "nproc",
    ]

    for cmd in commands:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out:
            print(f"  {cmd:45s} => {out}")
        if err:
            print(f"  {cmd:45s} ERR => {err}")

    client.close()
    print("\nSSH connection test PASSED!")

except Exception as e:
    print(f"CONNECTION FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
