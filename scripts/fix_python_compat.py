import paramiko
import re

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run_sudo(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(f"sudo bash -c '{cmd}'", timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# Fix Python 3.9 incompatible type annotations
# dict | List is Python 3.10+ syntax, need Union[dict, List[dict]]
print("=== Fixing Python 3.9 type annotations ===")

# Find all files with the dict | List pattern
out, err = run_sudo("grep -rn 'dict | List\\|list | dict\\|str | int\\|int | str\\|dict | str\\|str | dict\\|tuple | list\\|list | tuple' /www/server/panel/class/ 2>/dev/null | head -30")
print(f"Found patterns:\n{out}")

# Use sed to fix common.py
# Replace dict | List[dict] with Union[dict, List[dict]]
fixes = [
    ("s/dict | List\\[dict\\]/Union[dict, List[dict]]/g", "/www/server/panel/class/public/common.py"),
]

for sed_cmd, filepath in fixes:
    out, err = run_sudo(f"sed -i '{sed_cmd}' {filepath}")
    if err:
        print(f"ERR fixing {filepath}: {err}")

# Also check if Union is imported
out, err = run_sudo("grep 'from typing import' /www/server/panel/class/public/common.py | head -3")
print(f"\nTyping imports: {out}")

# Add Union if not present
out, err = run_sudo(
    "grep -q 'from typing import.*Union' /www/server/panel/class/public/common.py || "
    "sed -i 's/from typing import/from typing import Union,/' /www/server/panel/class/public/common.py"
)
print(f"Union added: {out}")

# Verify fix
out, err = run_sudo("grep -n 'find_value_by_key' /www/server/panel/class/public/common.py | head -1")
print(f"Fixed line: {out}")

client.close()
