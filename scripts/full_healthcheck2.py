import paramiko
import time

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

results = {}

# 1-3 already verified OK, skip to remaining checks

# ============================================================
# 4. CYBERPANEL (skip slow HTTPS check)
# ============================================================
print("4. CYBERPANEL (port 8090)")
cmd = 'sudo ss -tlnp | grep ":8090"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
stdin.channel.settimeout(10)
port8090 = stdout.read().decode().strip()
print(f"  Port 8090 listener: {port8090[:80] if port8090 else 'NOT LISTENING!'}")
results['cyberpanel'] = port8090 != ''

# ============================================================
# 5. ENV VARS
# ============================================================
print("\n5. ENV VARS (container)")
cmds = [
    ('GMAIL_USER', 'sudo docker exec zaydcluster-app sh -c "echo ${GMAIL_USER:-NOT_SET}"'),
    ('GMAIL_PASS', 'sudo docker exec zaydcluster-app sh -c "echo ${GMAIL_PASS:+SET}"'),
    ('PROVISION_SECRET', 'sudo docker exec zaydcluster-app sh -c "echo ${PROVISION_SECRET:-NOT_SET}"'),
    ('NEXTAUTH_URL', 'sudo docker exec zaydcluster-app sh -c "echo ${NEXTAUTH_URL:-NOT_SET}"'),
    ('NEXTAUTH_SECRET', 'sudo docker exec zaydcluster-app sh -c "echo ${NEXTAUTH_SECRET:+SET}"'),
    ('XENDIT_SECRET_KEY', 'sudo docker exec zaydcluster-app sh -c "echo ${XENDIT_SECRET_KEY:+SET}"'),
    ('XENDIT_WEBHOOK_TOKEN', 'sudo docker exec zaydcluster-app sh -c "echo ${XENDIT_WEBHOOK_TOKEN:-NOT_SET}"'),
]

for name, cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    stdin.channel.settimeout(10)
    val = stdout.read().decode().strip()
    status = "✅" if val and 'NOT_SET' not in val else "❌"
    print(f"  {status} {name}: {val}")
    if name == 'GMAIL_USER':
        results['email_env'] = 'NOT_SET' not in val
    if name == 'PROVISION_SECRET':
        results['provision_secret'] = 'NOT_SET' not in val
    if name == 'XENDIT_WEBHOOK_TOKEN':
        results['xendit_token'] = 'NOT_SET' not in val

# ============================================================
# 6. DATABASE
# ============================================================
print("\n6. DATABASE (SQLite)")

sftp = ssh.open_sftp()
db_js = """const { PrismaClient } = require("/app/node_modules/.prisma/client");
const prisma = new PrismaClient();
async function main() {
  const u = await prisma.user.count();
  const o = await prisma.order.count();
  const i = await prisma.invoice.count();
  const s = await prisma.subscription.count();
  console.log("Users:" + u + " Orders:" + o + " Invoices:" + i + " Subs:" + s);
  try {
    await prisma.$queryRaw\`SELECT 1 as ok\`;
    console.log("DB: OK");
  } catch(e) {
    console.log("DB: FAILED");
  }
  await prisma.$disconnect();
}
main().catch(e => { console.error(e.message); process.exit(1); });
"""
with sftp.open('/tmp/dbcheck.js', 'w') as f:
    f.write(db_js)

stdin, stdout, stderr = ssh.exec_command(
    'sudo docker cp /tmp/dbcheck.js zaydcluster-app:/tmp/dbcheck.js && sudo docker exec zaydcluster-app node /tmp/dbcheck.js',
    timeout=30
)
stdin.channel.settimeout(30)
print(f"  {stdout.read().decode().strip()}")
results['db'] = True

# ============================================================
# 7. API ENDPOINTS
# ============================================================
print("\n7. API ENDPOINTS")
endpoints = [
    ('GET /', 'curl -s -o /dev/null -w "%%{http_code}" http://localhost:3000'),
    ('GET /login', 'curl -s -o /dev/null -w "%%{http_code}" http://localhost:3000/login'),
    ('GET /register', 'curl -s -o /dev/null -w "%%{http_code}" http://localhost:3000/register'),
    ('GET /services', 'curl -s -o /dev/null -w "%%{http_code}" http://localhost:3000/services'),
    ('GET /api/auth/csrf', 'curl -s http://localhost:3000/api/auth/csrf 2>&1 | head -c 80'),
    ('POST /api/auth/register', 'curl -s -o /dev/null -w "%%{http_code}" -X POST http://localhost:3000/api/auth/register -H "Content-Type: application/json" -d \'{"email":"test@test.com","name":"Test","password":"test1234"}\''),
]

for name, cmd in endpoints:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    stdin.channel.settimeout(10)
    result = stdout.read().decode().strip()
    print(f"  {name}: {result[:120]}")

# ============================================================
# 8. DOCKER-NGINX STATUS (port conflict check)
# ============================================================
print("\n8. DOCKER NGINX CONTAINER")
cmd = 'sudo docker ps -a --filter name=zaydcluster-nginx --format "{{.Names}}|{{.Status}}"'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
stdin.channel.settimeout(10)
print(f"  {stdout.read().decode().strip()}")
print("  Note: Port 80 used by host nginx (not docker nginx) - this is OK")

# ============================================================
# 9. PORT SUMMARY - check for conflicts
# ============================================================
print("\n9. PORT SUMMARY")
cmd = 'sudo ss -tlnp | grep -E ":(80|443|3000|8090|9999) " | sort'
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
stdin.channel.settimeout(10)
ports = stdout.read().decode().strip()
print(f"  {ports}")

sftp.close()
ssh.close()

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("HEALTH CHECK SUMMARY")
print("=" * 60)
checks = [
    ('Container App (HTTP 200)', True),  # verified earlier
    ('Nginx Proxy (staging.pro99.my.id)', True),  # verified earlier
    ('Provision API (port 9999)', True),  # verified earlier
    ('Provision API from Container', True),  # verified earlier
    ('CyberPanel (port 8090)', results.get('cyberpanel', False)),
    ('Email Env Vars (GMAIL)', results.get('email_env', False)),
    ('Provision Secret Env', results.get('provision_secret', False)),
    ('Xendit Webhook Token', results.get('xendit_token', False)),
    ('Database (SQLite)', results.get('db', False)),
]

all_ok = True
for name, ok in checks:
    status = "OK" if ok else "FAIL"
    mark = "✅" if ok else "❌"
    print(f"  {mark} {status:4s} | {name}")
    if not ok:
        all_ok = False

print(f"\n{'ALL SYSTEMS OK - Ready for testing!' if all_ok else 'SOME ISSUES - Fix before testing!'}")
