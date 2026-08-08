import paramiko

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

# Check the theme_config.py issue
cmds = [
    "sudo grep -n 'clean_cahce\\|clean_cache' /www/server/panel/class_v2/theme_config.py | head -10",
    "sudo sed -n '125,135p' /www/server/panel/class_v2/theme_config.py",
    "sudo sed -n '675,685p' /www/server/panel/class_v2/theme_config.py",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    print(stdout.read().decode().strip())
    print('---')

client.close()
