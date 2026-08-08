import paramiko

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

# Direct sed commands to fix Python 3.9 type annotations
cmds = [
    # Add Union to typing imports if not already there
    "sudo sed -i 's/from typing import \\([^U]\\)/from typing import Union, \\1/' /www/server/panel/class/public/common.py",
    # Fix dict | List[dict] -> Union[dict, List[dict]]
    "sudo sed -i 's/dict | List\\[dict\\]/Union[dict, List[dict]]/g' /www/server/panel/class/public/common.py",
    # Check for other | type annotations
    "sudo grep -n ' | ' /www/server/panel/class/public/common.py | grep 'def \\|->' | head -10",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    out = stdout.read().decode().strip()
    print(f">>> {cmd[:80]}")
    print(out)
    print()

client.close()
