import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Use the bundled prisma from node_modules (not npx which installs latest)
print("=== Running Prisma DB Push (bundled) ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app node /app/node_modules/.prisma/engines/proxy-darwin 2>&1 || sudo docker exec zaydcluster-app node /app/node_modules/prisma/build/index.js db push 2>&1 | head -30',
    timeout=30
)
stdin.channel.settimeout(30)
print(stdout.read().decode().strip() or stderr.read().decode().strip())

# Alternative: just use the prisma client to create tables via raw SQL
print("\n=== Creating tables via raw SQL ===")
sftp = ssh.open_sftp()

# Read schema to understand tables needed
schema_sql = r"""
const { PrismaClient } = require("/app/node_modules/.prisma/client");
const prisma = new PrismaClient();

async function main() {
  try {
    // Just try to count - if table exists it works, if not we get error
    const count = await prisma.user.count();
    console.log("TABLES_EXIST:" + count);
  } catch(e) {
    console.log("TABLES_MISSING:" + e.message.substring(0, 200));
  }
  await prisma.$disconnect();
}
main();
"""

with sftp.open('/tmp/check_tables.js', 'w') as f:
    f.write(schema_sql)

stdin, stdout, stderr = ssh.exec_command(
    'sudo docker cp /tmp/check_tables.js zaydcluster-app:/tmp/check_tables.js && sudo docker exec zaydcluster-app node /tmp/check_tables.js 2>&1',
    timeout=15
)
stdin.channel.settimeout(15)
print(stdout.read().decode().strip())

sftp.close()
ssh.close()
