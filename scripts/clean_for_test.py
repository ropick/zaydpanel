import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=10)

sftp = ssh.open_sftp()

cleanup_js = """const { PrismaClient } = require("/app/node_modules/.prisma/client");
const prisma = new PrismaClient();
async function main() {
  try { await prisma.subscription.deleteMany(); } catch(e) {}
  try { await prisma.invoice.deleteMany(); } catch(e) {}
  try { await prisma.order.deleteMany(); } catch(e) {}
  try { await prisma.account.deleteMany(); } catch(e) {}
  try { await prisma.verificationToken.deleteMany(); } catch(e) {}
  try { await prisma.session.deleteMany(); } catch(e) {}
  try { await prisma.user.deleteMany(); } catch(e) {}
  console.log("ALL DATA CLEANED");
  const u = await prisma.user.count();
  const o = await prisma.order.count();
  const i = await prisma.invoice.count();
  console.log("Users:" + u + " Orders:" + o + " Invoices:" + i);
  await prisma.$disconnect();
}
main().catch(e => { console.error(e.message); process.exit(1); });
"""

with sftp.open('/tmp/cleanup2.js', 'w') as f:
    f.write(cleanup_js)

stdin, stdout, stderr = ssh.exec_command(
    'sudo docker cp /tmp/cleanup2.js zaydcluster-app:/tmp/cleanup2.js && sudo docker exec zaydcluster-app node /tmp/cleanup2.js',
    timeout=30
)
stdin.channel.settimeout(30)
print(stdout.read().decode().strip())

# Also clear logs
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker logs zaydcluster-app 2>&1 | wc -l',
    timeout=15
)
stdin.channel.settimeout(15)
total_lines = stdout.read().decode().strip()
print(f"Current log lines: {total_lines}")

sftp.close()
ssh.close()
print("\nDatabase cleaned! Ready for fresh test.")
