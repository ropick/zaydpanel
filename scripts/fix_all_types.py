import paramiko

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

# Fix all Python 3.10+ union type annotations  
# Pattern: SomeType | AnotherType -> Union[SomeType, AnotherType]
fixes = [
    "sed -i 's/List\\[str\\] | Set\\[str\\]/Union[List[str], Set[str]]/g' /www/server/panel/class/public/common.py",
    "sed -i 's/str | int/Union[str, int]/g' /www/server/panel/class/public/common.py",
    "sed -i 's/int | str/Union[int, str]/g' /www/server/panel/class/public/common.py",
    "sed -i 's/dict | str/Union[dict, str]/g' /www/server/panel/class/public/common.py",
    "sed -i 's/str | dict/Union[str, dict]/g' /www/server/panel/class/public/common.py",
]

for cmd in fixes:
    stdin, stdout, stderr = client.exec_command(f"sudo {cmd}", timeout=10)
    stderr.read()  # drain

# Add Set import if needed
stdin, stdout, stderr = client.exec_command(
    "sudo grep -q 'from typing import.*Set' /www/server/panel/class/public/common.py || "
    "sudo sed -i 's/from typing import Union,/from typing import Union, Set,/' /www/server/panel/class/public/common.py",
    timeout=10
)

# Verify no more | type annotations remain  
stdin, stdout, stderr = client.exec_command(
    "sudo grep -n ' | ' /www/server/panel/class/public/common.py | grep 'def \\|-> ' | head -10",
    timeout=10
)
remaining = stdout.read().decode().strip()
print(f"Remaining issues:\n{remaining or 'NONE - All fixed!'}")

# Check all imports
stdin, stdout, stderr = client.exec_command(
    "sudo grep 'from typing import' /www/server/panel/class/public/common.py | head -3",
    timeout=10
)
print(f"\nTyping imports: {stdout.read().decode().strip()}")

client.close()
