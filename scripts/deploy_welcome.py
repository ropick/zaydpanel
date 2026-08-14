#!/usr/bin/env python3
"""Deploy welcome page to existing sites and update agent."""
import paramiko, time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key = paramiko.Ed25519Key.from_private_key_file("/home/z/my-project/.ssh/oci_key")
client.connect("168.110.210.148", username="opc", pkey=key, timeout=15)

def run(cmd, sudo=False, timeout=15):
    if sudo: cmd = f"sudo bash -c '%s'" % cmd.replace("'", "'\\''")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err

WELCOME_HTML = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Selamat Datang - {domain}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.container{max-width:560px;width:100%;text-align:center}
.logo{display:inline-flex;align-items:center;gap:10px;font-size:24px;font-weight:700;color:#fff;margin-bottom:32px}
.logo-icon{width:44px;height:44px;background:linear-gradient(135deg,#06b6d4,#0891b2);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px}
h1{font-size:28px;font-weight:700;color:#fff;margin-bottom:8px}
.domain{font-size:18px;color:#06b6d4;font-weight:600;margin-bottom:24px}
.msg{font-size:15px;color:#94a3b8;line-height:1.7;margin-bottom:32px;max-width:440px;margin-left:auto;margin-right:auto}
.card{background:#1e293b;border:1px solid #334155;border-radius:16px;padding:24px;margin-bottom:24px}
.card-row{display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #334155}
.card-row:last-child{border-bottom:none}
.card-label{font-size:13px;color:#64748b}
.card-value{font-size:13px;color:#e2e8f0;font-weight:500}
.status{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;background:#065f46;color:#34d399}
.actions{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:8px;padding:10px 20px;border-radius:10px;font-size:14px;font-weight:600;text-decoration:none;transition:all .2s}
.btn-primary{background:linear-gradient(135deg,#06b6d4,#0891b2);color:#fff}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 4px 20px rgba(6,182,212,.3)}
.btn-secondary{background:#1e293b;color:#e2e8f0;border:1px solid #334155}
.btn-secondary:hover{background:#334155}
.footer{margin-top:32px;font-size:12px;color:#475569}
.footer a{color:#06b6d4;text-decoration:none}
</style>
</head>
<body>
<div class="container">
<div class="logo">
<div class="logo-icon">Z</div>
ZaydPanel
</div>
<h1>Selamat Datang!</h1>
<p class="domain">{domain}</p>
<p class="msg">Website Anda berhasil aktif. Halaman ini adalah halaman default yang dapat Anda ganti dengan file Anda sendiri melalui File Manager di panel.</p>
<div class="card">
<div class="card-row">
<span class="card-label">Status</span>
<span class="status">Aktif</span>
</div>
<div class="card-row">
<span class="card-label">Web Server</span>
<span class="card-value">Nginx + PHP-FPM</span>
</div>
<div class="card-row">
<span class="card-label">Panel</span>
<span class="card-value">ZaydPanel v3.0</span>
</div>
<div class="card-row">
<span class="card-label">Document Root</span>
<span class="card-value">/home/{domain}/public_html</span>
</div>
</div>
<div class="actions">
<a href="#" class="btn btn-primary">Login ke Panel</a>
<a href="#" class="btn btn-secondary">Upload File Anda</a>
</div>
<p class="footer">Dikelola oleh <a href="https://github.com/ropick/zaydpanel" target="_blank">ZaydPanel</a> &mdash; Free &amp; Open Source Hosting Control Panel</p>
</div>
</body>
</html>"""

# Find existing sites from nginx configs
out, _ = run("ls /etc/nginx/conf.d/*.conf 2>/dev/null | xargs -I{} basename {} .conf | grep -v -E '^(00-|php-fpm|default|example|shared|_)'", sudo=True)
sites = [s.strip() for s in out.strip().split('\n') if s.strip()]
print(f"Found sites: {sites}")

for domain in sites:
    home = f"/home/{domain}/public_html"
    html = WELCOME_HTML.replace("{domain}", domain)
    # Create dir if not exists
    run(f"mkdir -p {home}", sudo=True)
    # Write welcome page
    _, err = run(f"cat > {home}/index.html << 'HTMLEOF'\n{html}\nHTMLEOF", sudo=True)
    status = "OK" if not err else f"ERR: {err}"
    print(f"  {domain}: {status}")

print("Done.")
client.close()
