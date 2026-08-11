import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

sftp = ssh.open_sftp()

# Create admin user via node script
# ADMIN_EMAIL from .env = ropickaplikasi@gmail.com
admin_js = """const { PrismaClient } = require("/app/node_modules/.prisma/client");
const bcrypt = require("/app/node_modules/bcryptjs");
const prisma = new PrismaClient();
async function main() {
  // Check if admin exists
  const existing = await prisma.user.findFirst({ where: { role: 'admin' } });
  if (existing) {
    console.log("Admin already exists:", existing.email, "| ID:", existing.id);
    await prisma.$disconnect();
    return;
  }
  
  // Create admin
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
  console.log("Admin created successfully!");
  console.log("Email:", admin.email);
  console.log("Password: Zayd12345");
  console.log("Role:", admin.role);
  console.log("ID:", admin.id);
  await prisma.$disconnect();
}
main().catch(e => { console.error(e.message); process.exit(1); });
"""

with sftp.open('/tmp/create_admin.js', 'w') as f:
    f.write(admin_js)

stdin, stdout, stderr = ssh.exec_command(
    'sudo docker cp /tmp/create_admin.js zaydcluster-app:/tmp/create_admin.js && sudo docker exec zaydcluster-app node /tmp/create_admin.js',
    timeout=30
)
stdin.channel.settimeout(30)
result = stdout.read().decode().strip()
print(result)

# Verify
print("\n=== Verify admin ===")
verify_js = """const { PrismaClient } = require("/app/node_modules/.prisma/client");
const prisma = new PrismaClient();
async function main() {
  const admin = await prisma.user.findFirst({ where: { role: 'admin' } });
  if (admin) {
    console.log("Admin found: " + admin.email + " | Role: " + admin.role + " | ID: " + admin.id);
  } else {
    console.log("No admin found!");
  }
  await prisma.$disconnect();
}
main();
"""
with sftp.open('/tmp/verify_admin.js', 'w') as f:
    f.write(verify_js)

stdin, stdout, stderr = ssh.exec_command(
    'sudo docker cp /tmp/verify_admin.js zaydcluster-app:/tmp/verify_admin.js && sudo docker exec zaydcluster-app node /tmp/verify_admin.js',
    timeout=15
)
stdin.channel.settimeout(15)
print(stdout.read().decode().strip())

sftp.close()
ssh.close()
