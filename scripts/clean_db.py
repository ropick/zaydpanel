import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=10)

# Use sh (not bash) and write script file to container first via SFTP
sftp = ssh.open_sftp()

# Upload cleanup script
cleanup_js = """const { PrismaClient } = require("/app/node_modules/.prisma/client");
const prisma = new PrismaClient();
async function main() {
  try {
    await prisma.subscription.deleteMany({});
    console.log("Subscriptions deleted");
  } catch(e) { console.log("No subscriptions table"); }

  try {
    await prisma.invoice.deleteMany({});
    console.log("Invoices deleted");
  } catch(e) { console.log("No invoices table"); }

  try {
    await prisma.orderItem.deleteMany({});
    console.log("OrderItems deleted");
  } catch(e) { console.log("No orderItems table"); }

  try {
    await prisma.order.deleteMany({});
    console.log("Orders deleted");
  } catch(e) { console.log("No orders table"); }

  try {
    await prisma.account.deleteMany({});
    console.log("Accounts deleted");
  } catch(e) { console.log("No accounts table"); }

  try {
    await prisma.verificationToken.deleteMany({});
    console.log("VerificationTokens deleted");
  } catch(e) { console.log("No verificationTokens table"); }

  try {
    await prisma.session.deleteMany({});
    console.log("Sessions deleted");
  } catch(e) { console.log("No sessions table"); }

  try {
    await prisma.user.deleteMany({});
    console.log("Users deleted");
  } catch(e) { console.log("No users table"); }

  console.log("ALL DATA CLEANED");
  await prisma.$disconnect();
}
main().catch(e => { console.error(e.message); process.exit(1); });
"""

with sftp.open('/tmp/cleanup.js', 'w') as f:
    f.write(cleanup_js)

print("=== Uploading cleanup script and executing ===")

# Copy script into container and run
cmds = [
    'sudo docker cp /tmp/cleanup.js zaydcluster-app:/tmp/cleanup.js',
    'sudo docker exec zaydcluster-app node /tmp/cleanup.js',
    'sudo docker exec zaydcluster-app rm /tmp/cleanup.js',
]

for cmd in cmds:
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out:
        print(f"  OUT: {out}")
    if err:
        print(f"  ERR: {err}")

# Verify counts
print("\n=== Verify counts ===")
verify_js = """const { PrismaClient } = require("/app/node_modules/.prisma/client");
const prisma = new PrismaClient();
async function main() {
  const users = await prisma.user.count();
  const orders = await prisma.order.count();
  const invoices = await prisma.invoice.count();
  console.log("Users:", users, "Orders:", orders, "Invoices:", invoices);
  await prisma.$disconnect();
}
main().catch(e => { console.error(e.message); process.exit(1); });
"""

with sftp.open('/tmp/verify.js', 'w') as f:
    f.write(verify_js)

stdin, stdout, stderr = ssh.exec_command('sudo docker cp /tmp/verify.js zaydcluster-app:/tmp/verify.js && sudo docker exec zaydcluster-app node /tmp/verify.js && sudo docker exec zaydcluster-app rm /tmp/verify.js', timeout=60)
out = stdout.read().decode().strip()
err = stderr.read().decode().strip()
print(f"  {out}")
if err:
    print(f"  ERR: {err}")

sftp.close()
ssh.close()
print("\nDone!")
