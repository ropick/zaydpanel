import paramiko

key_path = '/home/z/my-project/.ssh/oci_key'
host = '168.110.210.148'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file(key_path)
ssh.connect(host, username='opc', pkey=key, timeout=30)
sftp = ssh.open_sftp()

# ============================================================
# 1. Update layout.tsx - change favicon from external URL to local files
# ============================================================
layout_path = '/opt/zaydcluster/src/app/layout.tsx'
with sftp.open(layout_path, 'r') as f:
    layout_content = f.read().decode()

# Replace external icon with local circular favicon
old_icons = """  icons: {
    icon: "https://z-cdn.chatglm.cn/z-ai/static/logo.svg",
  },"""

new_icons = """  icons: {
    icon: [
      { url: "/favicon-16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: "/apple-touch-icon.png",
  },"""

if old_icons in layout_content:
    layout_content = layout_content.replace(old_icons, new_icons)
    print("OK: layout.tsx icons updated to local circular favicons")
else:
    print("WARNING: Could not find old icons block in layout.tsx")

with sftp.open(layout_path, 'w') as f:
    f.write(layout_content)

# ============================================================
# 2. Update page.tsx - replace Server icon logo with circular Image
# ============================================================
page_path = '/opt/zaydcluster/src/app/page.tsx'
with sftp.open(page_path, 'r') as f:
    page_content = f.read().decode()

# 2a. Desktop navbar logo (line ~207-213)
old_navbar_logo = """            {/* Logo */}
          <a href="#hero" className="flex items-center gap-2">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-emerald-500 flex items-center justify-center">
              <Server className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
            </div>
            <span className="text-lg sm:text-xl font-bold text-foreground">
              zaydcluster<span className="text-emerald-500">.com</span>
            </span>
          </a>"""

new_navbar_logo = """            {/* Logo */}
          <a href="#hero" className="flex items-center gap-2">
            <img
              src="/logo-64.png"
              alt="ZaydCluster"
              className="w-8 h-8 sm:w-10 sm:h-10 rounded-full object-cover"
            />
            <span className="text-lg sm:text-xl font-bold text-foreground">
              zaydcluster<span className="text-emerald-500">.com</span>
            </span>
          </a>"""

if old_navbar_logo in page_content:
    page_content = page_content.replace(old_navbar_logo, new_navbar_logo)
    print("OK: Desktop navbar logo updated to circular image")
else:
    print("WARNING: Could not find desktop navbar logo")

# 2b. Mobile menu logo (line ~245-250)
old_mobile_logo = """                    <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
                      <Server className="w-5 h-5 text-white" />
                    </div>
                    <span className="font-bold text-foreground">
                      zaydcluster<span className="text-emerald-500">.com</span>
                    </span>"""

new_mobile_logo = """                    <img
                      src="/logo-64.png"
                      alt="ZaydCluster"
                      className="w-8 h-8 rounded-full object-cover"
                    />
                    <span className="font-bold text-foreground">
                      zaydcluster<span className="text-emerald-500">.com</span>
                    </span>"""

if old_mobile_logo in page_content:
    page_content = page_content.replace(old_mobile_logo, new_mobile_logo)
    print("OK: Mobile menu logo updated to circular image")
else:
    print("WARNING: Could not find mobile menu logo")

# 2c. Footer logo (line ~1139-1144)
old_footer_logo = """            <a href="#hero" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
                <Server className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold text-foreground">
                zaydcluster<span className="text-emerald-500">.com</span>
              </span>
            </a>"""

new_footer_logo = """            <a href="#hero" className="flex items-center gap-2">
              <img
                src="/logo-64.png"
                alt="ZaydCluster"
                className="w-8 h-8 rounded-full object-cover"
              />
              <span className="text-lg font-bold text-foreground">
                zaydcluster<span className="text-emerald-500">.com</span>
              </span>
            </a>"""

if old_footer_logo in page_content:
    page_content = page_content.replace(old_footer_logo, new_footer_logo)
    print("OK: Footer logo updated to circular image")
else:
    print("WARNING: Could not find footer logo")

with sftp.open(page_path, 'w') as f:
    f.write(page_content)

# ============================================================
# 3. Check if Server icon import is still needed (for features section)
# ============================================================
# Count remaining Server references (should still be used in features/stats)
server_count = page_content.count('Server')
print(f"\nRemaining 'Server' references in page.tsx: {server_count} (used in features/stats section)")

sftp.close()
ssh.close()
print("\nAll code updated!")
