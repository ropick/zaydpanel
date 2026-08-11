import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

vol_path = '/var/lib/docker/volumes/deploy_app-data/_data'

# Check existing files
stdin, stdout, stderr = ssh.exec_command(f'sudo ls -la {vol_path}/ 2>&1', timeout=10)
stdin.channel.settimeout(10)
print(f"Volume contents: {stdout.read().decode().strip()}")

sftp = ssh.open_sftp()

# Create all tables
create_sql = """
CREATE TABLE IF NOT EXISTS User (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  phone TEXT,
  password TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'client',
  emailVerified DATETIME,
  createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS Session (
  id TEXT PRIMARY KEY,
  sessionToken TEXT NOT NULL UNIQUE,
  userId TEXT NOT NULL,
  expires DATETIME NOT NULL,
  FOREIGN KEY (userId) REFERENCES User(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "Order" (
  id TEXT PRIMARY KEY,
  orderNumber TEXT NOT NULL UNIQUE,
  userId TEXT NOT NULL,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT NOT NULL,
  package TEXT NOT NULL,
  billingCycle TEXT NOT NULL DEFAULT 'monthly',
  domain TEXT,
  message TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  totalAmount REAL NOT NULL,
  cpUsername TEXT,
  cpPassword TEXT,
  cpDomain TEXT,
  createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (userId) REFERENCES User(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS Invoice (
  id TEXT PRIMARY KEY,
  invoiceNumber TEXT NOT NULL UNIQUE,
  orderId TEXT NOT NULL,
  userId TEXT NOT NULL,
  amount REAL NOT NULL,
  tax REAL NOT NULL DEFAULT 0,
  totalAmount REAL NOT NULL,
  status TEXT NOT NULL DEFAULT 'unpaid',
  dueDate DATETIME NOT NULL,
  paidAt DATETIME,
  paymentMethod TEXT,
  paymentRef TEXT,
  notes TEXT,
  createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (orderId) REFERENCES "Order"(id) ON DELETE CASCADE,
  FOREIGN KEY (userId) REFERENCES User(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS Subscription (
  id TEXT PRIMARY KEY,
  userId TEXT NOT NULL,
  orderId TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'active',
  billingCycle TEXT NOT NULL DEFAULT 'monthly',
  amount REAL NOT NULL,
  nextBilling DATETIME NOT NULL,
  createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (userId) REFERENCES User(id) ON DELETE CASCADE,
  FOREIGN KEY (orderId) REFERENCES "Order"(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS HostingOrder (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT,
  package TEXT NOT NULL,
  domain TEXT,
  message TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS ContactMessage (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  subject TEXT,
  message TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'unread',
  createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

with sftp.open('/tmp/create_tables.sql', 'w') as f:
    f.write(create_sql)

print("=== Creating tables ===")
stdin, stdout, stderr = ssh.exec_command(
    f'sudo sqlite3 {vol_path}/custom.db < /tmp/create_tables.sql 2>&1',
    timeout=15
)
stdin.channel.settimeout(15)
r = stdout.read().decode().strip()
e = stderr.read().decode().strip()
print(f"  {r or e}")

# Verify tables
stdin, stdout, stderr = ssh.exec_command(
    f'sudo sqlite3 {vol_path}/custom.db ".tables" 2>&1',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"  Tables: {stdout.read().decode().strip()}")

# Create admin with bcrypt hashed password "Zayd12345"
# Pre-computed hash: $2a$12$LJ3m4ys3Dz1i5vKyJSXL5.rFT2xOqX1nECPn4YQFMqJCQSZK7OqNa
# But we need to generate it properly. Use node with bcrypt.
print("\n=== Creating admin user ===")
hash_js = """const bcrypt = require("/app/node_modules/bcryptjs"); 
bcrypt.hash("Zayd12345", 12).then(h => console.log(h));"""

with sftp.open('/tmp/hash.js', 'w') as f:
    f.write(hash_js)

stdin, stdout, stderr = ssh.exec_command(
    'sudo docker cp /tmp/hash.js zaydcluster-app:/tmp/hash.js && sudo docker exec zaydcluster-app node /tmp/hash.js 2>&1',
    timeout=15
)
stdin.channel.settimeout(15)
pw_hash = stdout.read().decode().strip()
print(f"  Password hash: {pw_hash}")

if pw_hash.startswith('$2a$'):
    # Insert admin
    import shlex
    sql = f"INSERT INTO User (id, email, name, phone, password, role) VALUES ('admin-001', 'ropickaplikasi@gmail.com', 'Administrator', '081234567890', '{pw_hash}', 'admin');"
    
    stdin, stdout, stderr = ssh.exec_command(
        f"sudo sqlite3 {vol_path}/custom.db '{sql}' 2>&1",
        timeout=10
    )
    stdin.channel.settimeout(10)
    print(f"  Insert result: {stdout.read().decode().strip() or stderr.read().decode().strip()}")
    
    # Verify
    stdin, stdout, stderr = ssh.exec_command(
        f'sudo sqlite3 {vol_path}/custom.db "SELECT id, email, role FROM User;" 2>&1',
        timeout=10
    )
    stdin.channel.settimeout(10)
    print(f"  Users: {stdout.read().decode().strip()}")

# Set proper permissions on db file
stdin, stdout, stderr = ssh.exec_command(
    f'sudo chown 1001:1001 {vol_path}/custom.db 2>&1',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"\n  Permissions fixed: {stdout.read().decode().strip() or stderr.read().decode().strip()}")

sftp.close()
ssh.close()
print("\nDone!")
