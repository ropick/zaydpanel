import paramiko
import time
import json

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

results = {}

# ============================================================
# 1. CONTAINER APP - Check status, errors, logs
# ============================================================
print("=" * 60)
print("1. CONTAINER APP (zaydcluster-app)")
print("=" * 60)

cmd = 'sudo docker ps --filter name=zaydcluster-app --format "{{.Names}}|{{.Status}}|{{.Ports}}"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
info = stdout.read().decode().strip()
print(f"  Status: {info}")

cmd = 'sudo docker logs zaydcluster-app --tail 20 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
logs = stdout.read().decode().strip()
errors = [l for l in logs.split('\n') if 'error' in l.lower() or 'warn' in l.lower()]
print(f"  Recent errors/warnings: {len(errors)}")
for e in errors:
    print(f"    {e[:150]}")
print(f"  Last 3 log lines:")
for l in logs.split('\n')[-3:]:
    print(f"    {l[:150]}")

# Test app responds on port 3000
cmd = 'curl -s -o /dev/null -w "%{http_code}" http://localhost:3000'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
http_code = stdout.read().decode().strip()
print(f"  HTTP response (port 3000): {http_code}")
results['app'] = http_code == '200'

# ============================================================
# 2. NGINX PROXY
# ============================================================
print("\n" + "=" * 60)
print("2. NGINX PROXY (host)")
print("=" * 60)

cmd = 'sudo ss -tlnp | grep ":80 "'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
port80 = stdout.read().decode().strip()
print(f"  Port 80 listener: {port80[:100]}")

cmd = 'curl -s -o /dev/null -w "%{http_code}" http://localhost:80'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
http_nginx = stdout.read().decode().strip()
print(f"  HTTP response (port 80): {http_nginx}")

cmd = 'curl -s -o /dev/null -w "%{http_code}" https://staging.pro99.my.id 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
https_staging = stdout.read().decode().strip()
print(f"  HTTPS staging.pro99.my.id: {https_staging}")
results['nginx'] = http_nginx == '200'

# ============================================================
# 3. PROVISION API (host port 9999)
# ============================================================
print("\n" + "=" * 60)
print("3. PROVISION API (port 9999)")
print("=" * 60)

cmd = 'sudo systemctl status provision-api --no-pager 2>&1 | head -15'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
svc_status = stdout.read().decode().strip()
print(f"  Service status:")
for l in svc_status.split('\n'):
    print(f"    {l[:120]}")

cmd = 'sudo ss -tlnp | grep ":9999"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
port9999 = stdout.read().decode().strip()
print(f"  Port 9999 listener: {port9999[:100] if port9999 else 'NOT LISTENING!'}")

# Test provision API health
cmd = 'curl -s -X POST http://127.0.0.1:9999/health -H "Content-Type: application/json" -d \'{}\' 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
prov_health = stdout.read().decode().strip()
print(f"  Health check response: {prov_health[:200]}")
results['provision_port'] = bool(port9999)

# Test from inside container
cmd = 'sudo docker exec zaydcluster-app wget -qO- --timeout=5 http://host.docker.internal:9999/health 2>&1 || echo "FAILED_FROM_CONTAINER"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=20)
stdin.channel.settimeout(20)
from_container = stdout.read().decode().strip()
print(f"  From container (host.docker.internal:9999): {from_container[:200]}")
results['provision_from_container'] = 'FAILED' not in from_container

# ============================================================
# 4. CYBERPANEL
# ============================================================
print("\n" + "=" * 60)
print("4. CYBERPANEL (port 8090)")
print("=" * 60)

cmd = 'sudo ss -tlnp | grep ":8090"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
port8090 = stdout.read().decode().strip()
print(f"  Port 8090 listener: {port8090[:100] if port8090 else 'NOT LISTENING!'}")

cmd = 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8090 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
cp_http = stdout.read().decode().strip()
print(f"  HTTP response (port 8090): {cp_http}")

cmd = 'curl -s -o /dev/null -w "%{http_code}" https://panel.pro99.my.id:8090 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
cp_https = stdout.read().decode().strip()
print(f"  HTTPS panel.pro99.my.id:8090: {cp_https}")
results['cyberpanel'] = port8090 != ''

# ============================================================
# 5. EMAIL (GMAIL SMTP)
# ============================================================
print("\n" + "=" * 60)
print("5. EMAIL (GMAIL SMTP)")
print("=" * 60)

# Check GMAIL env vars are set
cmd = 'sudo docker exec zaydcluster-app sh -c "echo GMAIL_USER=${GMAIL_USER:-NOT_SET} | head -c 50" 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
gmail_user = stdout.read().decode().strip()
print(f"  GMAIL_USER in container: {gmail_user}")

cmd = 'sudo docker exec zaydcluster-app sh -c "echo GMAIL_PASS=${GMAIL_PASS:+SET}" 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
gmail_pass = stdout.read().decode().strip()
print(f"  GMAIL_PASS in container: {gmail_pass}")
results['email_env'] = 'NOT_SET' not in gmail_user and 'SET' in gmail_pass

# Check PROVISION_SECRET env
cmd = 'sudo docker exec zaydcluster-app sh -c "echo PROVISION_SECRET=${PROVISION_SECRET:-NOT_SET}" 2>&1'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
stdin.channel.settimeout(15)
prov_secret = stdout.read().decode().strip()
print(f"  PROVISION_SECRET in container: {prov_secret}")
results['provision_secret'] = 'NOT_SET' not in prov_secret

# ============================================================
# 6. DATABASE
# ============================================================
print("\n" + "=" * 60)
print("6. DATABASE (SQLite)")
print("=" * 60)

db_js = """const { PrismaClient } = require("/app/node_modules/.prisma/client");
const prisma = new PrismaClient();
async function main() {
  const u = await prisma.user.count();
  const o = await prisma.order.count();
  const i = await prisma.invoice.count();
  const s = await prisma.subscription.count();
  console.log("Users:" + u + " Orders:" + o + " Invoices:" + i + " Subs:" + s);
  try {
    await prisma.$queryRaw`SELECT 1 as ok`;
    console.log("DB connection: OK");
  } catch(e) {
    console.log("DB connection: FAILED - " + e.message);
  }
  await prisma.$disconnect();
}
main().catch(e => { console.error(e.message); process.exit(1); });
"""

sftp = ssh.open_sftp()
with sftp.open('/tmp/dbcheck.js', 'w') as f:
    f.write(db_js)
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker cp /tmp/dbcheck.js zaydcluster-app:/tmp/dbcheck.js && sudo docker exec zaydcluster-app node /tmp/dbcheck.js',
    timeout=30
)
stdin.channel.settimeout(30)
db_result = stdout.read().decode().strip()
print(f"  {db_result}")
results['db'] = 'OK' in db_result

# ============================================================
# 7. API ENDPOINTS
# ============================================================
print("\n" + "=" * 60)
print("7. API ENDPOINTS")
print("=" * 60)

endpoints = [
    ('GET /', 'curl -s -o /dev/null -w "%{http_code}" http://localhost:3000'),
    ('GET /login', 'curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/login'),
    ('GET /register', 'curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/register'),
    ('GET /api/auth/csrf', 'curl -s http://localhost:3000/api/auth/csrf 2>&1 | head -c 100'),
    ('POST /api/auth/register (empty)', 'curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:3000/api/auth/register -H "Content-Type: application/json" -d \'{}\''),
]

for name, cmd in endpoints:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
    stdin.channel.settimeout(15)
    result = stdout.read().decode().strip()
    print(f"  {name}: {result[:120]}")

sftp.close()
ssh.close()

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("HEALTH CHECK SUMMARY")
print("=" * 60)
checks = [
    ('Container App HTTP', results.get('app', False)),
    ('Nginx Proxy', results.get('nginx', False)),
    ('Provision API Port 9999', results.get('provision_port', False)),
    ('Provision API from Container', results.get('provision_from_container', False)),
    ('CyberPanel', results.get('cyberpanel', False)),
    ('Email Env Vars', results.get('email_env', False)),
    ('Provision Secret Env', results.get('provision_secret', False)),
    ('Database', results.get('db', False)),
]

all_ok = True
for name, ok in checks:
    status = "✅ OK" if ok else "❌ FAIL"
    print(f"  {status}  {name}")
    if not ok:
        all_ok = False

print(f"\n{'🎉 ALL SYSTEMS OK - Ready for testing!' if all_ok else '⚠️ SOME ISSUES FOUND - Fix before testing!'}")
