import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=10)
sftp = ssh.open_sftp()

# ============ 1. UPDATE email.ts ============
# Replace hostingReadyEmail function to include credentials
email_path = '/opt/zaydcluster/src/lib/email.ts'
with sftp.open(email_path, 'r') as fh:
    email_content = fh.read().decode()

# Find the hostingReadyEmail function and replace it
old_func = """// ====== Hosting Ready Email ======
export function hostingReadyEmail(
  customerName: string,
  domain: string,
  packageType: string,
  orderNumber: string
): string {
  return `
    <head><meta charset="utf-8"></head>
    <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
      <div style="background:linear-gradient(135deg,#1e40af 0%,#3b82f6 100%);padding:30px;text-align:center;border-radius:10px 10px 0 0;">
        <h1 style="color:white;margin:0;">ZaydCluster</h1>
        <p style="color:rgba(255,255,255,0.9);margin:10px 0 0;">Hosting Siap Digunakan!</p>
      </div>
      <div style="background:#f8f9fa;padding:30px;border:1px solid #e9ecef;border-radius:0 0 10px 10px;">
        <p>Halo <strong>${customerName}</strong>,</p>
        <p>Hosting Anda telah berhasil di-aktifkan!</p>
        
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#eff6ff;">
            <td style="padding:12px;border:1px solid #dbeafe;font-weight:bold;">Domain</td>
            <td style="padding:12px;border:1px solid #dbeafe;"><strong>${domain}</strong></td>
          </tr>
          <tr>
            <td style="padding:12px;border:1px solid #e5e7eb;font-weight:bold;">Paket</td>
            <td style="padding:12px;border:1px solid #e5e7eb;">${packageType}</td>
          </tr>
          <tr style="background:#eff6ff;">
            <td style="padding:12px;border:1px solid #dbeafe;font-weight:bold;">Order</td>
            <td style="padding:12px;border:1px solid #dbeafe;">${orderNumber}</td>
          </tr>
          <tr>
            <td style="padding:12px;border:1px solid #e5e7eb;font-weight:bold;">Server</td>
            <td style="padding:12px;border:1px solid #e5e7eb;">Oracle ARM (Indonesia)</td>
          </tr>
        </table>
        
        <h3 style="color:#1e40af;">Langkah Selanjutnya:</h3>
        <ol style="color:#475569;line-height:2;">
          <li>Login ke dashboard ZaydCluster</li>
          <li>Upload website Anda ke folder <code style="background:#f1f5f9;padding:2px 6px;border-radius:4px;">public_html</code></li>
          <li>Jika pakai custom domain, arahkan DNS A record ke server kami</li>
        </ol>
        
        <div style="text-align:center;margin-top:30px;">
          <a href="https://staging.pro99.my.id" style="background:#1e40af;color:white;padding:12px 30px;border-radius:8px;text-decoration:none;font-weight:bold;">Buka Dashboard</a>
        </div>
        
        <p style="margin-top:30px;color:#64748b;font-size:13px;">
          Jika ada pertanyaan, hubungi support kami.<br>
          ZaydCluster - Shared Hosting Indonesia
        </p>
      </div>
    </body>
  `;
}"""

new_func = """// ====== Hosting Ready Email (with credentials) ======
export function hostingReadyEmail(
  customerName: string,
  domain: string,
  packageType: string,
  orderNumber: string,
  cpUsername?: string,
  cpPassword?: string
): string {
  const panelUrl = 'https://panel.pro99.my.id';
  const hasCreds = cpUsername && cpPassword;

  return `
    <head><meta charset="utf-8"></head>
    <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
      <div style="background:linear-gradient(135deg,#1e40af 0%,#3b82f6 100%);padding:30px;text-align:center;border-radius:10px 10px 0 0;">
        <h1 style="color:white;margin:0;">ZaydCluster</h1>
        <p style="color:rgba(255,255,255,0.9);margin:10px 0 0;">Hosting Siap Digunakan!</p>
      </div>
      <div style="background:#f8f9fa;padding:30px;border:1px solid #e9ecef;border-radius:0 0 10px 10px;">
        <h2 style="color:#1e40af;margin-top:0;">Selamat, ${customerName}!</h2>
        <p>Hosting Anda telah berhasil di-aktifkan. Berikut detail layanan Anda:</p>
        
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#eff6ff;">
            <td style="padding:12px;border:1px solid #dbeafe;font-weight:bold;">Domain</td>
            <td style="padding:12px;border:1px solid #dbeafe;"><strong>${domain}</strong></td>
          </tr>
          <tr>
            <td style="padding:12px;border:1px solid #e5e7eb;font-weight:bold;">Paket</td>
            <td style="padding:12px;border:1px solid #e5e7eb;">${packageType}</td>
          </tr>
          <tr style="background:#eff6ff;">
            <td style="padding:12px;border:1px solid #dbeafe;font-weight:bold;">Order</td>
            <td style="padding:12px;border:1px solid #dbeafe;">${orderNumber}</td>
          </tr>
          <tr>
            <td style="padding:12px;border:1px solid #e5e7eb;font-weight:bold;">Server</td>
            <td style="padding:12px;border:1px solid #e5e7eb;">Oracle ARM (Indonesia)</td>
          </tr>
        </table>

        ${hasCreds ? `
        <div style="background:#fffbeb;border:2px solid #f59e0b;border-radius:10px;padding:20px;margin:25px 0;">
          <h3 style="color:#92400e;margin-top:0;display:flex;align-items:center;gap:8px;">
            <span style="font-size:20px;">&#128274;</span> Login Panel Hosting (CyberPanel)
          </h3>
          <p style="color:#78350f;margin-bottom:15px;">Gunakan credentials berikut untuk login ke panel hosting Anda:</p>
          
          <table style="width:100%;border-collapse:collapse;margin:10px 0;">
            <tr>
              <td style="padding:10px;border:1px solid #fde68a;font-weight:bold;background:#fef3c7;">URL Panel</td>
              <td style="padding:10px;border:1px solid #fde68a;">
                <a href="${panelUrl}" style="color:#1e40af;word-break:break-all;">${panelUrl}</a>
              </td>
            </tr>
            <tr>
              <td style="padding:10px;border:1px solid #fde68a;font-weight:bold;background:#fef3c7;">Username</td>
              <td style="padding:10px;border:1px solid #fde68a;">
                <code style="background:#fff;padding:4px 8px;border-radius:4px;font-size:14px;">${cpUsername}</code>
              </td>
            </tr>
            <tr>
              <td style="padding:10px;border:1px solid #fde68a;font-weight:bold;background:#fef3c7;">Password</td>
              <td style="padding:10px;border:1px solid #fde68a;">
                <code style="background:#fff;padding:4px 8px;border-radius:4px;font-size:14px;">${cpPassword}</code>
              </td>
            </tr>
          </table>
          
          <div style="text-align:center;margin-top:20px;">
            <a href="${panelUrl}" style="background:#1e40af;color:white;padding:12px 30px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;">Login ke Panel Hosting</a>
          </div>
        </div>
        
        <div style="background:#fef2f2;border-left:4px solid #ef4444;padding:15px;margin:20px 0;border-radius:0 8px 8px 0;">
          <p style="margin:0;color:#991b1b;font-size:13px;">
            <strong>Penting:</strong> Simpan username dan password ini dengan baik. Anda bisa mengubah password setelah login ke panel.
          </p>
        </div>
        ` : ''}
        
        <h3 style="color:#1e40af;">Langkah Selanjutnya:</h3>
        <ol style="color:#475569;line-height:2;">
          <li>Login ke panel hosting dengan credentials di atas</li>
          <li>Upload website Anda ke folder <code style="background:#f1f5f9;padding:2px 6px;border-radius:4px;">public_html</code></li>
          <li>Jika pakai custom domain, arahkan DNS A record ke server kami</li>
        </ol>
        
        <div style="text-align:center;margin-top:30px;">
          <a href="https://staging.pro99.my.id" style="background:#1e40af;color:white;padding:12px 30px;border-radius:8px;text-decoration:none;font-weight:bold;">Buka Dashboard ZaydCluster</a>
        </div>
        
        <p style="margin-top:30px;color:#64748b;font-size:13px;">
          Jika ada pertanyaan, hubungi support kami.<br>
          ZaydCluster - Shared Hosting Indonesia
        </p>
      </div>
    </body>
  `;
}"""

if old_func in email_content:
    email_content = email_content.replace(old_func, new_func)
    print("SUCCESS: hostingReadyEmail replaced with credentials version")
else:
    print("WARNING: Could not find exact match for old hostingReadyEmail function")
    print("Trying alternative approach...")

with sftp.open(email_path, 'w') as fh:
    fh.write(email_content)

# ============ 2. UPDATE callback/route.ts ============
cb_path = '/opt/zaydcluster/src/app/api/payment/callback/route.ts'
with sftp.open(cb_path, 'r') as fh:
    cb_content = fh.read().decode()

# Replace the hostingReadyEmail call to include credentials
old_call = """            await sendEmail({
              to: invoice.user.email,
              subject: `[ZaydCluster] Hosting Anda Aktif - ${effectiveDomain}`,
              html: hostingReadyEmail(invoice.user.name, effectiveDomain, invoice.order.package, invoice.order.orderNumber),
            });"""

new_call = """            // Send hosting ready email WITH credentials
            await sendEmail({
              to: invoice.user.email,
              subject: `[ZaydCluster] Hosting Aktif - Login Credentials ${effectiveDomain}`,
              html: hostingReadyEmail(
                invoice.user.name,
                effectiveDomain,
                invoice.order.package,
                invoice.order.orderNumber,
                creds.username,
                creds.password
              ),
            });"""

if old_call in cb_content:
    cb_content = cb_content.replace(old_call, new_call)
    print("SUCCESS: callback updated to pass credentials to email")
else:
    print("WARNING: Could not find exact match for old hostingReadyEmail call")

with sftp.open(cb_path, 'w') as fh:
    fh.write(cb_content)

sftp.close()
ssh.close()
print("\nDone! Both files updated on server.")
