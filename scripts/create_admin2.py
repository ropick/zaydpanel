import paramiko
import json

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

sftp = ssh.open_sftp()

# Create admin - using simpler approach
admin_js = r"""
const { PrismaClient } = require("/app/node_modules/.prisma/client");
const bcrypt = require("/app/node_modules/bcryptjs");
const prisma = new PrismaClient();

async function main() {
  try {
    const existing = await prisma.user.findFirst({ where: { role: "admin" } });
    if (existing) {
      console.log("EXISTS:" + existing.email + "|" + existing.role + "|" + existing.id);
      await prisma.$disconnect();
      return;
    }
    
    const hashedPassword = await bcrypt.hash("Zayd12345", 12);
    const admin = await prisma.user.create({
      data: {
        name: "Administrator",
        email: "ropickaplikasi@gmail.com",
        phone: "081234567890",
        password: hashedPassword,
        role: "admin",
      },
    });
    console.log("CREATED:" + admin.email + "|" + admin.role + "|" + admin.id);
    await prisma.$disconnect();
  } catch(e) {
    console.error("ERROR:" + e.message);
    process.exit(1);
  }
}
main();
"""

with sftp.open('/tmp/admin2.js', 'w') as f:
    f.write(admin_js)

# Upload and run
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker cp /tmp/admin2.js zaydcluster-app:/tmp/admin2.js 2>&1',
    timeout=15
)
stdin.channel.settimeout(15)
print("Copy:", stdout.read().decode().strip(), stderr.read().decode().strip())

stdin, stdout, stderr = ssh.exec_command(
    'sudo docker exec zaydcluster-app node /tmp/admin2.js 2>&1',
    timeout=30
)
stdin.channel.settimeout(30)
out = stdout.read().decode().strip()
err = stderr.read().decode().strip()
print("Result:", out)
if err:
    print("Stderr:", err)

sftp.close()
ssh.close()
