import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)

# Find the database file location
print("=== Finding database file ===")
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker volume inspect app-data 2>&1 | grep Mountpoint',
    timeout=10
)
stdin.channel.settimeout(10)
vol_path = stdout.read().decode().strip()
print(f"Volume: {vol_path}")

# Extract mountpoint path
stdin, stdout, stderr = ssh.exec_command(
    'sudo docker volume inspect app-data --format "{{.Mountpoint}}" 2>&1',
    timeout=10
)
stdin.channel.settimeout(10)
mountpoint = stdout.read().decode().strip()
print(f"Mountpoint: {mountpoint}")

# Check if db file exists
stdin, stdout, stderr = ssh.exec_command(
    f'sudo ls -la {mountpoint}/ 2>&1',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"Files: {stdout.read().decode().strip()}")

# Create tables using host sqlite3
create_tables_sql = """
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

sftp = ssh.open_sftp()
with sftp.open('/tmp/create_tables.sql', 'w') as f:
    f.write(create_tables_sql)

print(f"\n=== Creating tables via host sqlite3 ===")
stdin, stdout, stderr = ssh.exec_command(
    f'sudo sqlite3 {mountpoint}/custom.db < /tmp/create_tables.sql 2>&1',
    timeout=15
)
stdin.channel.settimeout(15)
print(f"Result: {stdout.read().decode().strip() or stderr.read().decode().strip()}")

# Verify
stdin, stdout, stderr = ssh.exec_command(
    f'sudo sqlite3 {mountpoint}/custom.db ".tables" 2>&1',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"Tables: {stdout.read().decode().strip()}")

# Now create admin user
print("\n=== Creating admin user ===")
stdin, stdout, stderr = ssh.exec_command(
    f"sudo sqlite3 {mountpoint}/custom.db \"INSERT INTO User (id, email, name, phone, password, role) VALUES ('admin-001', 'ropickaplikasi@gmail.com', 'Administrator', '081234567890', '\$2a\$12\$LJ3m4ys3Dz1i5vKyJSXL5.rFT2xOqX1nECPn4YQFMqJCQSZK7OqNa', 'admin');\" 2>&1",
    timeout=10
)
stdin.channel.settimeout(10)
result = stdout.read().decode().strip()
err = stderr.read().decode().strip()
print(f"Insert: {result or err}")

# Verify admin
stdin, stdout, stderr = ssh.exec_command(
    f'sudo sqlite3 {mountpoint}/custom.db "SELECT id, email, role FROM User WHERE role=\'admin\';" 2>&1',
    timeout=10
)
stdin.channel.settimeout(10)
print(f"Admin: {stdout.read().decode().strip()}")

sftp.close()
ssh.close()
