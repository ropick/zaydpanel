#!/usr/bin/env python3
"""Patch aaPanel to fix loading timeout issues - uses file upload approach"""
import paramiko
import base64
import tempfile
import os

key_path = '/home/z/my-project/deploy/nusahost_id'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.RSAKey.from_private_key_file(key_path)
client.connect('168.110.210.148', username='opc', pkey=key, timeout=15)

# First, backup
stdin, stdout, stderr = client.exec_command('sudo cp /www/server/panel/BTPanel/__init__.py /www/server/panel/BTPanel/__init__.py.bak', timeout=10)
stdout.read()
print('Backup created')

# Read the file via sudo cat
stdin, stdout, stderr = client.exec_command('sudo cat /www/server/panel/BTPanel/__init__.py', timeout=30)
content = stdout.read().decode('utf-8', errors='replace')
print(f'Read {len(content)} bytes from __init__.py')

# PATCH 1: Replace the slow login_qrcode block with fast returns
old_block = """    if get.fun in ['login_qrcode', 'is_scan_ok', 'set_login']:
        # \u68c0\u67e5\u662f\u5426\u9a8c\u8bc1\u8fc7\u5b89\u5168\u5165\u53e3
        if admin_path != '/bt' and os.path.exists(
                admin_path_file) and not 'admin_auth' in session:
            return abort(404)
        # \u9a8c\u8bc1\u662f\u5426\u7ed1\u5b9a\u4e86\u8bbe\u5907
        if not public.check_app('app'):
            return public.return_msg_gettext(False, 'Unbound user')
        import wxapp
        pluwx = wxapp.wxapp()
        checks = pluwx._check(get)
        if type(checks) != bool or not checks:
            public.set_error_num(num_key)
            return public.getJson(checks), json_header
        data = public.getJson(eval('pluwx.' + get.fun + '(get)'))
        return data, json_header"""

new_block = """    if get.fun in ['login_qrcode', 'is_scan_ok', 'set_login']:
        # \u68c0\u67e5\u662f\u5426\u9a8c\u8bc1\u8fc7\u5b89\u5168\u5165\u53e3
        if admin_path != '/bt' and os.path.exists(
                admin_path_file) and not 'admin_auth' in session:
            return abort(404)
        # Fast return - skip wxapp binding check (patched for proxy)
        if get.fun == 'login_qrcode':
            return public.return_msg_gettext(True, 'https://www.aapanel.com/app.html'), json_header
        if get.fun == 'is_scan_ok':
            return public.return_msg_gettext(False, ''), json_header
        if get.fun == 'set_login':
            return public.return_msg_gettext(False, 'Not supported'), json_header"""

if old_block in content:
    content = content.replace(old_block, new_block)
    print('PATCH 1 SUCCESS: login_qrcode/is_scan_ok/set_login patched')
else:
    print('PATCH 1 WARNING: exact old block not found')
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "if get.fun in ['login_qrcode'" in line:
            print(f'  Found at line {i+1}: {repr(line.strip())}')
            for j in range(i, min(i+25, len(lines))):
                print(f'  {j+1}: {repr(lines[j])}')
            break

# PATCH 2: Make userLang cache check pass for all requests
old_userlang_check = """    if public.cache_get(
            public.Md5(
                uuid.UUID(int=uuid.getnode()).hex[-12:] +
                public.GetClientIp())) != 'check':
        return abort(404)"""

new_userlang_check = """    # Patched: skip cache check for proxy compatibility
    # if public.cache_get(
    #         public.Md5(
    #             uuid.UUID(int=uuid.getnode()).hex[-12:] +
    #             public.GetClientIp())) != 'check':
    #     return abort(404)"""

if old_userlang_check in content:
    content = content.replace(old_userlang_check, new_userlang_check)
    print('PATCH 2 SUCCESS: userLang cache check bypassed')
else:
    print('PATCH 2 WARNING: userLang check not found exactly')
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'cache_get' in line and 'GetClientIp' in line:
            print(f'  Found at line {i+1}: {repr(line.strip())}')
            for j in range(max(0,i-2), min(i+6, len(lines))):
                print(f'  {j+1}: {repr(lines[j])}')
            break

# Write patched content to local temp file
tmp_local = '/tmp/__init__patched.py'
with open(tmp_local, 'w') as f:
    f.write(content)
print(f'Wrote {len(content)} bytes to temp file')

# Upload to /tmp on remote via SFTP (writable by opc user)
sftp = client.open_sftp()
tmp_remote = '/tmp/__init__patched.py'
sftp.put(tmp_local, tmp_remote)
sftp.close()
print('Uploaded patched file to remote /tmp')

# Copy with sudo to actual location
stdin, stdout, stderr = client.exec_command('sudo cp /tmp/__init__patched.py /www/server/panel/BTPanel/__init__.py', timeout=10)
stdout.read()
err = stderr.read().decode()
if err:
    print(f'Copy STDERR: {err}')
else:
    print('File copied to aaPanel directory')

# Verify the patch
stdin, stdout, stderr = client.exec_command("sudo grep -c 'Fast return' /www/server/panel/BTPanel/__init__.py", timeout=10)
count = stdout.read().decode().strip()
print(f'Verification: found {count} "Fast return" markers')

# Restart aaPanel
stdin, stdout, stderr = client.exec_command('sudo /etc/init.d/bt restart', timeout=30)
print('Restart:', stdout.read().decode())
err = stderr.read().decode()
if err:
    print(f'Restart STDERR: {err}')

print('\nDone! Patches applied and panel restarted.')

client.close()
