#!/usr/bin/env python3
"""Patch aaPanel v2 routes and userLang v2 to fix loading timeout"""
import paramiko

key_path = '/home/z/my-project/deploy/nusahost_id'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file(key_path)
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

# Read the file via sudo cat
stdin, stdout, stderr = client.exec_command('sudo cat /www/server/panel/BTPanel/__init__.py', timeout=30)
content = stdout.read().decode('utf-8', errors='replace')
print(f'Read {len(content)} bytes')

# PATCH 3: Replace v2 login_qrcode block (uses wxapp_v2)
old_v2 = """    if get.fun in ['login_qrcode', 'is_scan_ok', 'set_login']:
        # \u68c0\u67e5\u662f\u5426\u9a8c\u8bc1\u8fc7\u5b89\u5168\u5165\u53e3
        if admin_path != '/bt' and os.path.exists(
                admin_path_file) and not 'admin_auth' in session:
            return abort(404)
        # \u9a8c\u8bc1\u662f\u5426\u7ed1\u5b9a\u4e86\u8bbe\u5907
        if not public.check_app('app'):
            return public.return_msg_gettext(False, 'Unbound user')
        import wxapp_v2
        pluwx = wxapp_v2.wxapp()
        checks = pluwx._check(get)
        if type(checks) != bool or not checks:
            public.set_error_num(num_key)
            return public.getJson(checks), json_header
        data = public.getJson(eval('pluwx.' + get.fun + '(get)'))
        return data, json_header"""

new_v2 = """    if get.fun in ['login_qrcode', 'is_scan_ok', 'set_login']:
        # \u68c0\u67e5\u662f\u5426\u9a8c\u8bc1\u8fc7\u5b89\u5168\u5165\u53e3
        if admin_path != '/bt' and os.path.exists(
                admin_path_file) and not 'admin_auth' in session:
            return abort(404)
        # Fast return - skip wxapp_v2 binding check (patched for proxy)
        if get.fun == 'login_qrcode':
            return public.return_msg_gettext(True, 'https://www.aapanel.com/app.html'), json_header
        if get.fun == 'is_scan_ok':
            return public.return_msg_gettext(False, ''), json_header
        if get.fun == 'set_login':
            return public.return_msg_gettext(False, 'Not supported'), json_header"""

if old_v2 in content:
    content = content.replace(old_v2, new_v2)
    print('PATCH 3 SUCCESS: v2 login_qrcode patched')
else:
    print('PATCH 3 WARNING: v2 old block not found')

# PATCH 4: Also check userLang v2
old_userlang_v2_check = """    # Patched: skip cache check for proxy compatibility
    # if public.cache_get(
    #         public.Md5(
    #             uuid.UUID(int=uuid.getnode()).hex[-12:] +
    #             public.GetClientIp())) != 'check':
    #     return abort(404)"""

# This was already patched - check if there's a second instance in the code
count = content.count('Patched: skip cache check')
print(f'Found {count} userLang patches already')

# Also check for userLang v2 function
if 'def userLang_v2():' in content or 'def userLang():' in content:
    # Check if there's a second userLang route with cache check
    remaining = content.count('GetClientIp')
    print(f'Remaining GetClientIp references: {remaining}')

# Write to local file
with open('/tmp/__init__patched2.py', 'w') as f:
    f.write(content)
print(f'Wrote {len(content)} bytes')

# Upload and copy
sftp = client.open_sftp()
sftp.put('/tmp/__init__patched2.py', '/tmp/__init__patched2.py')
sftp.close()

stdin, stdout, stderr = client.exec_command('sudo cp /tmp/__init__patched2.py /www/server/panel/BTPanel/__init__.py', timeout=10)
stdout.read()

# Verify
stdin, stdout, stderr = client.exec_command("sudo grep -c 'Fast return' /www/server/panel/BTPanel/__init__.py", timeout=10)
count = stdout.read().decode().strip()
print(f'Verification: {count} "Fast return" markers')

# Restart
stdin, stdout, stderr = client.exec_command('sudo /etc/init.d/bt restart', timeout=30)
print('Restart:', stdout.read().decode())

print('\nDone!')

client.close()
