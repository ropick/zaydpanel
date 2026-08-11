#!/usr/bin/env python3
import subprocess, os, sys, argparse, json, time, urllib.request, ssl, base64, secrets, string, datetime

CP_API = "https://127.0.0.1:8090/api"
CP_USER = "admin"
CP_PASS = os.environ.get("CP_ADMIN_PASS", "Zayd12345")
PKG_MAP = {"Starter": "Starter", "Business": "Business", "Premium": "Default"}

def run(cmd, sudo=True):
    prefix = "sudo " if sudo else ""
    r = subprocess.run(prefix + cmd, shell=True, capture_output=True, text=True, timeout=60)
    if r.returncode != 0 and r.stderr:
        print("  [WARN] " + r.stderr.strip()[:200])
    return r.stdout.strip()

def create_cyberpanel_site(domain, email, owner, password, package_name):
    payload = json.dumps({
        "adminUser": CP_USER, "adminPass": CP_PASS,
        "ownerEmail": email, "websiteOwner": owner, "ownerPassword": password,
        "domainName": domain, "packageName": package_name,
        "phpSelection": "PHP 8.4", "ssl": 1, "dkimCheck": 1, "openBasedir": 1
    }).encode()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(CP_API + "/createWebsite", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=180) as resp:
            result = json.loads(resp.read().decode())
            print("  CyberPanel API: " + str(result))
            return result.get("createWebSiteStatus") == 1, result
    except Exception as e:
        print("  CyberPanel Error: " + str(e))
        return False, {"error_message": str(e)}

def create_nginx_proxy(domain, alias):
    px = "server {\n    listen 80;\n    server_name " + alias + ";\n    location /.well-known/acme-challenge/ { root /var/www/certbot; }\n    location / {\n        proxy_pass http://127.0.0.1:8080;\n        proxy_http_version 1.1;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n        proxy_buffering off;\n    }\n}"
    conf_path = "/etc/nginx/conf.d/proxy-" + domain + ".conf"
    encoded = base64.b64encode(px.encode()).decode()
    run("echo '" + encoded + "' | base64 -d > " + conf_path)

def remove_nginx_proxy(domain):
    run("rm -f /etc/nginx/conf.d/proxy-" + domain + ".conf")

def reload_nginx():
    r = run("nginx -t 2>&1")
    if "syntax is ok" in r:
        run("systemctl reload nginx")
        return True
    print("  NGINX ERROR: " + r)
    return False

def create_default_page(domain, subdomain, package, order_number):
    pkgs = {"Starter": {"quota": "1G", "bw": "10G"}, "Business": {"quota": "5G", "bw": "50G"}, "Premium": {"quota": "20G", "bw": "Unlimited"}}
    p = pkgs.get(package, pkgs["Starter"])
    html = '<!DOCTYPE html><html lang="id"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>' + domain + '</title><style>body{font-family:sans-serif;margin:0;padding:40px;background:#f0f4f8}.c{max-width:640px;margin:auto;background:#fff;padding:40px;border-radius:12px}h1{color:#1e40af}</style></head><body><div class="c"><h1>Selamat Datang!</h1><p>Hosting <strong>' + domain + '</strong> aktif.</p><p>Paket: ' + package + ' | Order: ' + order_number + '</p></div></body></html>'
    home_dir = "/home/" + domain
    if os.path.exists(home_dir + "/public_html"):
        encoded = base64.b64encode(html.encode()).decode()
        run("echo '" + encoded + "' | base64 -d > " + home_dir + "/public_html/index.html")
        print("  Default page created")
    else:
        print("  WARNING: public_html not found at " + home_dir)

def provision(domain, subdomain, name, package, email, order_number):
    if domain:
        ed = domain
        alias = domain + " www." + domain
    else:
        ed = subdomain + ".pro99.my.id"
        alias = ed
    print("\n PROVISION: " + ed + " | " + name + " | " + package + " | " + order_number)
    chars = string.ascii_letters + string.digits + "!@#$%"
    cust_pass = ''.join(secrets.choice(chars) for _ in range(16))
    owner_name = subdomain[:20]
    cp_pkg = PKG_MAP.get(package, "Starter")
    print("  Creating site in CyberPanel...")
    success, result = create_cyberpanel_site(ed, email, owner_name, cust_pass, cp_pkg)
    if not success:
        print("  ERROR: " + result.get("error_message", "Unknown"))
        # Still output error credentials
        cred = {"success": False, "error": result.get("error_message", "Unknown")}
        print("CREDENTIALS_JSON:" + json.dumps(cred))
        return False
    create_nginx_proxy(ed, alias)
    if not reload_nginx():
        print("  WARNING: Nginx reload failed")
    time.sleep(2)
    create_default_page(ed, subdomain, package, order_number)
    print("  DONE: " + ed + " aktif!")
    cred = {"success": True, "domain": ed, "username": owner_name, "password": cust_pass, "package": package}
    print("CREDENTIALS_JSON:" + json.dumps(cred))
    return True

def deprovision(domain, subdomain):
    ed = domain if domain else subdomain + ".pro99.my.id"
    print("\n DEPROVISION: " + ed)
    remove_nginx_proxy(ed)
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        payload = json.dumps({"adminUser": CP_USER, "adminPass": CP_PASS, "domainName": ed, "websiteOwner": subdomain[:20]}).encode()
        req = urllib.request.Request(CP_API + "/deleteWebsite", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            print("  CyberPanel delete: OK")
    except Exception as e:
        print("  WARNING: " + str(e))
    reload_nginx()
    print("  DONE: " + ed + " removed")

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("provision")
    p.add_argument("--domain", default="")
    p.add_argument("--subdomain", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--package", required=True, choices=["Starter","Business","Premium"])
    p.add_argument("--email", required=True)
    p.add_argument("--order", required=True)
    d = sub.add_parser("deprovision")
    d.add_argument("--domain", default="")
    d.add_argument("--subdomain", required=True)
    args = parser.parse_args()
    if args.action == "provision":
        sys.exit(0 if provision(args.domain, args.subdomain, args.name, args.package, args.email, args.order) else 1)
    elif args.action == "deprovision":
        deprovision(args.domain, args.subdomain)

if __name__ == "__main__":
    main()
