import paramiko, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
k = paramiko.Ed25519Key.from_private_key_file('/home/z/my-project/.ssh/oci_key')
ssh.connect('168.110.210.148', username='opc', pkey=k)

for i in range(20):
    time.sleep(15)
    t = (i + 1) * 15
    
    stdin, stdout, _ = ssh.exec_command('docker ps --filter name=zaydcluster-app --format "{{.Status}}"')
    status = stdout.read().decode().strip()
    
    stdin2, stdout2, _ = ssh.exec_command('tail -1 /tmp/docker_rebuild.log 2>/dev/null')
    log = stdout2.read().decode().strip()
    
    if status:
        msg = '[%ds] Container UP: %s' % (t, status)
        print(msg)
        break
    
    if 'error' in log.lower() or 'failed' in log.lower():
        msg = '[%ds] BUILD FAILED: %s' % (t, log)
        print(msg)
        stdin3, stdout3, _ = ssh.exec_command('tail -10 /tmp/docker_rebuild.log')
        print(stdout3.read().decode())
        break
    
    msg = '[%ds] %s' % (t, log[:100])
    print(msg)

stdin, stdout, _ = ssh.exec_command('docker ps --filter name=zaydcluster-app --format "{{.Status}}"')
final = stdout.read().decode().strip()
print('\nFinal: %s' % final)

if final:
    stdin, stdout, _ = ssh.exec_command('curl -s -o /dev/null -w "%%{size_download}" http://localhost:3000/favicon-32.png')
    print('Favicon-32: %s bytes' % stdout.read().decode().strip())
    stdin, stdout, _ = ssh.exec_command('curl -s -o /dev/null -w "%%{size_download}" http://localhost:3000/logo-64.png')
    print('Logo-64: %s bytes' % stdout.read().decode().strip())

ssh.close()
