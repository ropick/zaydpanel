import paramiko

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

# Revert and fix properly - the original @clean_cahce() was correct for a factory pattern
# The problem is that clean_cahce is a @staticmethod which returns a decorator
# We need to remove @staticmethod from clean_cahce so it works as a factory

stdin, stdout, stderr = client.exec_command(
    "sudo sed -i 's/@clean_cahce$/@clean_cahce()/g' /www/server/panel/class_v2/theme_config.py",
    timeout=10
)

# Now remove @staticmethod from the clean_cahce definition
# The function should be a standalone function that returns a decorator
stdin, stdout, stderr = client.exec_command(
    "sudo sed -i '/^    @staticmethod$/,/^    def clean_cahce/{ /^    @staticmethod$/d }' /www/server/panel/class_v2/theme_config.py",
    timeout=10
)

# Verify
stdin, stdout, stderr = client.exec_command(
    "sudo sed -n '238,252p' /www/server/panel/class_v2/theme_config.py",
    timeout=10
)
print("After fix:")
print(stdout.read().decode().strip())

# Check usage
stdin, stdout, stderr = client.exec_command(
    "sudo grep -n 'clean_cahce' /www/server/panel/class_v2/theme_config.py",
    timeout=10
)
print("\nUsage:")
print(stdout.read().decode().strip())

client.close()
