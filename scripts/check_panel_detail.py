import paramiko

key_path = '/home/z/my-project/deploy/nusahost_id'
host = '168.110.210.148'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file(key_path, password=None)
client.connect(host, username='opc', pkey=key, timeout=15)

# The curl test returns 302 - meaning aaPanel is redirecting. Let's check WHERE it redirects to
# and also test with the security path in cookies

commands = [
    # Check redirect location
    ("Redirect Location", "curl -sI --max-time 10 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977/613ccb60/ 2>&1 | head -20"),
    
    # Check if panel responds to login path
    ("Login Page Test", "curl -s --max-time 15 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64)' http://127.0.0.1:36977/613ccb60/ 2>&1 | head -50"),
    
    # Check the security entry point
    ("Security Path File", "cat /www/server/panel/data/admin_path.pl"),
    
    # Check SSL config
    ("SSL Config", "cat /www/server/panel/data/ssl.pl"),
    
    # Check if panel is forcing HTTPS redirect
    ("Panel Config", "cat /www/server/panel/config/config.json 2>/dev/null || echo 'no config.json'"),
    
    # Check debug mode
    ("Debug Mode", "ls -la /www/server/panel/data/debug.pl 2>/dev/null && echo 'DEBUG ON' || echo 'DEBUG OFF'"),
    
    # Check panel port
    ("Panel Port", "cat /www/server/panel/data/port.pl 2>/dev/null"),
    
    # Docker nginx status
    ("Docker Nginx Status", "sudo docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' 2>/dev/null || docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' 2>/dev/null || echo 'Cannot access docker'"),
]

for label, cmd in commands:
    print(f"\n=== {label} ===")
    try:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=20)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if out:
            print(out)
        if err:
            print(f"STDERR: {err}")
    except Exception as e:
        print(f"ERROR: {e}")

client.close()
