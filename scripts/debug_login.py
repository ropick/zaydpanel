import paramiko

key = paramiko.RSAKey.from_private_key_file('/home/z/my-project/deploy/nusahost_id')
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

def run(cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode().strip(), stderr.read().decode().strip()

# Check Flask version
out, err = run("sudo /www/server/panel/pyenv/bin/python3 -c 'import flask; print(flask.__file__); print(flask.__version__)'")
print(f"Flask: {out}")

# The panel code login() might not return anything in GET for first visit
# Check what panelSetup().init() does
out, err = run("sudo grep -n 'class panelSetup' /www/server/panel/class/common.py | head -3")
print(f"panelSetup: {out}")

# Check the init method
out, err = run("sudo sed -n '50,100p' /www/server/panel/class/common.py")
print(f"init code:\n{out}")

client.close()
