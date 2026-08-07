import paramiko

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

# Look at the clean_cahce definition - it's a staticmethod but being used as @clean_cahce()
# This is a bug in aaPanel - it should either be a regular function or called without ()
cmds = [
    "sudo sed -n '238,250p' /www/server/panel/class_v2/theme_config.py",
    "sudo grep -c 'clean_cahce' /www/server/panel/class_v2/theme_config.py",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    print(stdout.read().decode().strip())
    print('---')

# Fix: Change @clean_cahce() to @clean_cahce everywhere in this file
stdin, stdout, stderr = client.exec_command(
    "sudo sed -i 's/@clean_cahce()/@clean_cahce/g' /www/server/panel/class_v2/theme_config.py",
    timeout=10
)
print("Fixed @clean_cahce() -> @clean_cahce")

# Verify
stdin, stdout, stderr = client.exec_command(
    "sudo grep 'clean_cahce' /www/server/panel/class_v2/theme_config.py | head -10",
    timeout=10
)
print(stdout.read().decode().strip())

client.close()
