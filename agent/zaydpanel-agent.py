#!/usr/bin/env python3
"""ZaydPanel Agent v3.0 - Full-featured hosting control panel agent.
Features: SQLite DB, JWT Auth, Multi-User ACL, Packages, Email, FTP, Statistics, Billing Webhook.
"""
import http.server, json, subprocess, os, sys, signal, socket, secrets, string, shutil, time, re, base64, glob, datetime, platform, hashlib, sqlite3, struct, csv, io
from socketserver import ThreadingMixIn
from pathlib import Path
from http.cookies import SimpleCookie

CONF = {
    "PORT": int(os.environ.get("ZAYDPANEL_AGENT_PORT", "8442")),
    "SECRET": os.environ.get("ZAYDPANEL_AGENT_SECRET", ""),
    "JWT_SECRET": os.environ.get("ZAYDPANEL_JWT_SECRET", ""),
    "SITES_DIR": "/home",
    "NGINX_CONF_DIR": "/etc/nginx/conf.d",
    "PHP_FPM_CONF_DIR": "/etc/php-fpm.d",
    "LOG_DIR": "/var/log/nginx",
    "BACKUP_DIR": "/opt/zaydpanel/backups",
    "CRON_DIR": "/opt/zaydpanel/cron",
    "DATA_DIR": "/opt/zaydpanel/data",
    "DB_PATH": "/opt/zaydpanel/data/zaydpanel.db",
    "PHP_VERSION": "8.3",
}

SYSTEM_CONF_PREFIXES = ("00-", "php-fpm", "default", "example", "shared", "_")

# ── SQLite Database ────────────────────────────────────────────────────────

def _init_db():
    """Initialize SQLite database with all required tables."""
    os.makedirs(os.path.dirname(CONF["DB_PATH"]), exist_ok=True)
    conn = sqlite3.connect(CONF["DB_PATH"])
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT DEFAULT '',
        full_name TEXT DEFAULT '',
        role TEXT DEFAULT 'customer',
        package_id INTEGER,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT (datetime('now')),
        last_login TEXT,
        notes TEXT DEFAULT ''
    )""")

    # Packages table
    c.execute("""CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        disk_quota TEXT DEFAULT '',
        bandwidth TEXT DEFAULT '',
        max_sites INTEGER DEFAULT 0,
        max_databases INTEGER DEFAULT 0,
        max_ftp INTEGER DEFAULT 0,
        max_email INTEGER DEFAULT 0,
        price_monthly REAL DEFAULT 0,
        description TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    # Sites ownership table
    c.execute("""CREATE TABLE IF NOT EXISTS site_owners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(domain, user_id)
    )""")

    # Email accounts
    c.execute("""CREATE TABLE IF NOT EXISTS email_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT NOT NULL,
        address TEXT NOT NULL,
        password TEXT DEFAULT '',
        quota_mb INTEGER DEFAULT 500,
        user_id INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(domain, address)
    )""")

    # FTP accounts
    c.execute("""CREATE TABLE IF NOT EXISTS ftp_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT DEFAULT '',
        home_dir TEXT DEFAULT '',
        user_id INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(username)
    )""")

    # Activity log
    c.execute("""CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT DEFAULT '',
        action TEXT NOT NULL,
        details TEXT DEFAULT '',
        ip TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    # Bandwidth stats
    c.execute("""CREATE TABLE IF NOT EXISTS bandwidth_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT NOT NULL,
        bytes_rx INTEGER DEFAULT 0,
        bytes_tx INTEGER DEFAULT 0,
        date TEXT NOT NULL,
        UNIQUE(domain, date)
    )""")

    # Billing webhooks
    c.execute("""CREATE TABLE IF NOT EXISTS webhook_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        payload TEXT DEFAULT '',
        status TEXT DEFAULT 'pending',
        attempts INTEGER DEFAULT 0,
        last_attempt TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    # Create default admin if not exists
    _admin_pw = os.environ.get("ZAYDPANEL_ADMIN_PASSWORD", "")
    admin_hash = _hash_password(_admin_pw) if _admin_pw else None
    if not admin_hash:
        # Generate random admin password and log it
        import secrets as _sec
        _admin_pw = _sec.token_urlsafe(16)
        admin_hash = _hash_password(_admin_pw)
        print(f"[INIT] Default admin password: {_admin_pw}")
        print("[INIT] Set ZAYDPANEL_ADMIN_PASSWORD env var to customize.")
    c.execute("SELECT id FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password_hash, email, full_name, role, status) VALUES (?,?,?,?,?,?)",
                  ("admin", admin_hash, "admin@localhost", "Administrator", "admin", "active"))

    # Create default packages if not exists
    for slug, name, disk, bw, sites, dbs, ftp, email, price in [
        ("starter", "Starter", "1G", "10G", 1, 1, 1, 1, 0),
        ("business", "Business", "10G", "100G", 5, 10, 5, 10, 49000),
        ("premium", "Premium", "50G", "Unlimited", 20, 50, 20, 50, 149000),
    ]:
        c.execute("SELECT id FROM packages WHERE slug=?", (slug,))
        if not c.fetchone():
            c.execute("""INSERT INTO packages (name,slug,disk_quota,bandwidth,max_sites,max_databases,max_ftp,max_email,price_monthly)
                         VALUES (?,?,?,?,?,?,?,?,?)""", (name, slug, disk, bw, sites, dbs, ftp, email, price))

    conn.commit()
    conn.close()


def _get_db():
    conn = sqlite3.connect(CONF["DB_PATH"])
    conn.row_factory = sqlite3.Row
    return conn


# ── Password & JWT ────────────────────────────────────────────────────────

def _hash_password(password):
    """Hash password with SHA-256 + salt."""
    salt = os.environ.get("ZAYDPANEL_PASSWORD_SALT", "")
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()


def _verify_password(password, password_hash):
    return _hash_password(password) == password_hash


def _jwt_encode(payload, expiry_hours=24):
    """Simple JWT-like token (base64 JSON)."""
    import time as _time
    payload["exp"] = int(_time.time()) + (expiry_hours * 3600)
    payload["iat"] = int(_time.time())
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = hashlib.sha256(f"{CONF['JWT_SECRET']}.{header}.{body}".encode()).hexdigest()[:32]
    return f"{header}.{body}.{sig}"


def _jwt_decode(token):
    """Decode JWT-like token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, sig = parts
        expected_sig = hashlib.sha256(f"{CONF['JWT_SECRET']}.{header}.{body}".encode()).hexdigest()[:32]
        if sig != expected_sig:
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + "=="))
        import time as _time
        if payload.get("exp", 0) < int(_time.time()):
            return None
        return payload
    except:
        return None


def _get_user_from_token(handler):
    """Extract user from X-User-Token header."""
    token = handler.headers.get("X-User-Token", "")
    if not token:
        return None
    payload = _jwt_decode(token)
    if not payload:
        return None
    return payload.get("user")


def _get_request_user(handler):
    """Get current user info from request token."""
    user_data = _get_user_from_token(handler)
    if not user_data:
        return None
    return user_data


def _is_admin(handler):
    """Check if current user is admin."""
    user = _get_request_user(handler)
    if not user:
        return False
    return user.get("role") == "admin"


def _log_activity(user_id, username, action, details="", ip=""):
    """Log an activity entry."""
    try:
        conn = _get_db()
        conn.execute("INSERT INTO activity_log (user_id, username, action, details, ip) VALUES (?,?,?,?,?)",
                     (user_id, username, action, details, ip))
        conn.commit()
        conn.close()
    except:
        pass


# ── Shell Helpers ──────────────────────────────────────────────────────────

def _run(cmd, check=True):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
    if check and result.returncode != 0:
        raise RuntimeError("Command failed: %s\n%s" % (cmd, result.stderr[:500]))
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def _run_json(cmd):
    out, err, rc = _run(cmd, check=False)
    try:
        return json.loads(out)
    except:
        return None


def _gen_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return "".join(secrets.choice(chars) for _ in range(length))


def _safe_domain(domain):
    return re.sub(r"[^a-zA-Z0-9.-]", "", domain).lower().strip(".")


def _site_home(domain):
    return "%s/%s" % (CONF["SITES_DIR"], domain)


def _site_nginx(domain):
    return "%s/%s.conf" % (CONF["NGINX_CONF_DIR"], domain)


def _response(handler, data, status=200):
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode())


def _error(handler, msg, status=400):
    _response(handler, {"success": False, "error": msg}, status)


def _ok(handler, data=None):
    _response(handler, {"success": True, "data": data})


def _read_body(handler):
    """Read JSON body from request."""
    try:
        length = int(handler.headers.get("Content-Length", 0))
        if length > 0:
            body = handler.rfile.read(length)
            return json.loads(body)
    except:
        pass
    return {}


# ── Site Helpers ──────────────────────────────────────────────────────────

def _is_proxy_config(conf_path):
    try:
        content = Path(conf_path).read_text()
        has_proxy = "proxy_pass" in content
        if has_proxy:
            lines = content.split("\n")
            for line in lines:
                if "root" in line and "/var/www/certbot" not in line and "well-known" not in line:
                    return False
            return True
    except:
        pass
    return False


def _get_php_fpm_pool_status(domain):
    pool_file = "%s/%s.conf" % (CONF["PHP_FPM_CONF_DIR"], domain)
    if os.path.exists(pool_file):
        try:
            out, _, _ = _run("pgrep -c php-fpm 2>/dev/null || echo 0", check=False)
            if int(out) > 0:
                return True
        except:
            pass
    try:
        out, _, _ = _run("systemctl is-active php-fpm 2>/dev/null || echo inactive", check=False)
        if out == "active":
            return True
    except:
        pass
    return False


def _get_site_php_version(domain):
    conf_path = _site_nginx(domain)
    try:
        content = Path(conf_path).read_text()
        match = re.search(r'php[.-]?(\d+\.\d+)', content)
        if match:
            return match.group(1)
    except:
        pass
    pool_file = "%s/%s.conf" % (CONF["PHP_FPM_CONF_DIR"], domain)
    try:
        content = Path(pool_file).read_text()
        match = re.search(r'php[.-]?(\d+\.\d+)', content)
        if match:
            return match.group(1)
    except:
        pass
    return CONF.get("PHP_VERSION", "8.3")


def _get_sites():
    sites = []
    nginx_dir = Path(CONF["NGINX_CONF_DIR"])
    if nginx_dir.exists():
        for f in sorted(nginx_dir.glob("*.conf")):
            domain = f.stem
            if domain.startswith(SYSTEM_CONF_PREFIXES):
                continue
            try:
                content = f.read_text()
            except:
                continue
            home_dir = _site_home(domain)
            has_home = os.path.isdir(home_dir)
            has_ssl = "ssl_certificate" in content
            has_wp = os.path.exists("%s/wp-login.php" % home_dir) if has_home else False
            has_index = os.path.exists("%s/index.php" % home_dir) or os.path.exists("%s/index.html" % home_dir) if has_home else False
            is_proxy = _is_proxy_config(str(f))
            php_ver = _get_site_php_version(domain) if has_home and not is_proxy else None
            php_fpm = _get_php_fpm_pool_status(domain) if has_home and not is_proxy else False
            site_type = "proxy" if is_proxy else ("wordpress" if has_wp else ("active" if has_home and has_index else "empty"))
            sites.append({
                "domain": domain, "home": home_dir, "exists": has_home,
                "ssl": has_ssl, "has_wp": has_wp, "php_version": php_ver,
                "type": site_type, "php_fpm": php_fpm,
            })
    return sites


def _get_user_sites(user_id):
    """Get sites owned by a specific user."""
    conn = _get_db()
    rows = conn.execute("SELECT domain FROM site_owners WHERE user_id=?", (user_id,)).fetchall()
    domains = [r["domain"] for r in rows]
    conn.close()
    if not domains:
        return []
    all_sites = _get_sites()
    return [s for s in all_sites if s["domain"] in domains]


def _fmt_net(bytes_val):
    bytes_val = int(bytes_val)
    if bytes_val >= 1073741824:
        return "%.1f GB" % (bytes_val / 1073741824)
    if bytes_val >= 1048576:
        return "%.1f MB" % (bytes_val / 1048576)
    if bytes_val >= 1024:
        return "%.1f KB" % (bytes_val / 1024)
    return "%d B" % bytes_val


# ── Auth Handlers ──────────────────────────────────────────────────────────

def handle_auth_login(handler, data):
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return _error(handler, "Username dan password wajib diisi")
    conn = _get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    if not user:
        return _error(handler, "Username atau password salah")
    if user["status"] != "active":
        return _error(handler, "Akun Anda ditangguhkan. Hubungi administrator.")
    if not _verify_password(password, user["password_hash"]):
        return _error(handler, "Username atau password salah")
    # Get package info
    conn = _get_db()
    pkg = conn.execute("SELECT id, name, slug FROM packages WHERE id=?", (user["package_id"],)).fetchone() if user["package_id"] else None
    conn.execute("UPDATE users SET last_login=datetime('now') WHERE id=?", (user["id"],))
    conn.commit()
    conn.close()
    token = _jwt_encode({"user": {"id": user["id"], "username": user["username"], "role": user["role"]}})
    _log_activity(user["id"], user["username"], "login", "User logged in", handler.client_address[0] if hasattr(handler, 'client_address') else "")
    _ok(handler, {
        "token": token,
        "user": {
            "id": user["id"], "username": user["username"], "role": user["role"],
            "email": user["email"], "full_name": user["full_name"],
            "package_id": user["package_id"],
            "package": {"name": pkg["name"], "slug": pkg["slug"]} if pkg else None,
            "status": user["status"], "created_at": user["created_at"],
            "last_login": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    })


def handle_auth_me(handler):
    user = _get_request_user(handler)
    if not user:
        return _error(handler, "Unauthorized", 401)
    conn = _get_db()
    u = conn.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone()
    pkg = conn.execute("SELECT id, name, slug FROM packages WHERE id=?", (u["package_id"],)).fetchone() if u["package_id"] else None
    conn.close()
    _ok(handler, {
        "id": u["id"], "username": u["username"], "role": u["role"],
        "email": u["email"], "full_name": u["full_name"],
        "package_id": u["package_id"],
        "package": {"name": pkg["name"], "slug": pkg["slug"]} if pkg else None,
        "status": u["status"], "created_at": u["created_at"], "last_login": u["last_login"],
    })


def handle_auth_change_password(handler, data):
    user = _get_request_user(handler)
    if not user:
        return _error(handler, "Unauthorized", 401)
    old_pw = data.get("old_password", "")
    new_pw = data.get("new_password", "")
    if not old_pw or not new_pw:
        return _error(handler, "Password lama dan baru wajib diisi")
    if len(new_pw) < 6:
        return _error(handler, "Password baru minimal 6 karakter")
    conn = _get_db()
    u = conn.execute("SELECT password_hash FROM users WHERE id=?", (user["id"],)).fetchone()
    if not _verify_password(old_pw, u["password_hash"]):
        conn.close()
        return _error(handler, "Password lama salah")
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (_hash_password(new_pw), user["id"]))
    conn.commit()
    conn.close()
    _log_activity(user["id"], user["username"], "change_password", "Password changed")
    _ok(handler, {"message": "Password berhasil diubah"})


def handle_list_users(handler):
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    conn = _get_db()
    rows = conn.execute("""SELECT u.*, p.name as package_name FROM users u
                           LEFT JOIN packages p ON u.package_id=p.id ORDER BY u.id""").fetchall()
    conn.close()
    users = []
    for r in rows:
        users.append({
            "id": r["id"], "username": r["username"], "email": r["email"],
            "full_name": r["full_name"], "role": r["role"],
            "package_id": r["package_id"], "package_name": r["package_name"],
            "status": r["status"], "created_at": r["created_at"], "last_login": r["last_login"],
        })
    _ok(handler, users)


def handle_create_user(handler, data):
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    username = data.get("username", "").strip().lower()
    password = data.get("password", _gen_password(12))
    email = data.get("email", "").strip()
    full_name = data.get("full_name", "").strip()
    role = data.get("role", "customer")
    package_id = data.get("package_id")
    if not username:
        return _error(handler, "Username wajib diisi")
    if not re.match(r'^[a-z0-9_]+$', username):
        return _error(handler, "Username hanya boleh huruf kecil, angka, dan underscore")
    if len(username) < 3:
        return _error(handler, "Username minimal 3 karakter")
    conn = _get_db()
    existing = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    if existing:
        conn.close()
        return _error(handler, "Username sudah digunakan")
    conn.execute("INSERT INTO users (username, password_hash, email, full_name, role, package_id) VALUES (?,?,?,?,?,?)",
                 (username, _hash_password(password), email, full_name, role, package_id))
    conn.commit()
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    admin = _get_request_user(handler)
    _log_activity(admin["id"], admin["username"], "create_user", f"Created user: {username}", handler.client_address[0] if hasattr(handler, 'client_address') else "")
    _ok(handler, {"id": user_id, "username": username, "password": password, "message": f"User {username} created with password: {password}"})


def handle_update_user(handler, data):
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    user_id = data.get("id")
    if not user_id:
        return _error(handler, "User ID wajib")
    conn = _get_db()
    u = conn.execute("SELECT id, username FROM users WHERE id=?", (user_id,)).fetchone()
    if not u:
        conn.close()
        return _error(handler, "User tidak ditemukan")
    fields = []
    values = []
    for key in ["email", "full_name", "role", "package_id", "status"]:
        if key in data:
            fields.append(f"{key}=?")
            values.append(data[key])
    if fields:
        values.append(user_id)
        conn.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=?", values)
        conn.commit()
    conn.close()
    admin = _get_request_user(handler)
    _log_activity(admin["id"], admin["username"], "update_user", f"Updated user: {u['username']}")
    _ok(handler, {"message": f"User {u['username']} updated"})


def handle_delete_user(handler, data):
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    user_id = data.get("id")
    if not user_id:
        return _error(handler, "User ID wajib")
    conn = _get_db()
    u = conn.execute("SELECT id, username FROM users WHERE id=?", (user_id,)).fetchone()
    if not u:
        conn.close()
        return _error(handler, "User tidak ditemukan")
    if u["username"] == "admin":
        conn.close()
        return _error(handler, "Tidak bisa hapus admin utama")
    conn.execute("DELETE FROM site_owners WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM email_accounts WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM ftp_accounts WHERE user_id=?", (user_id,))
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    admin = _get_request_user(handler)
    _log_activity(admin["id"], admin["username"], "delete_user", f"Deleted user: {u['username']}")
    _ok(handler, {"message": f"User {u['username']} deleted"})


def handle_reset_password(handler, data):
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    user_id = data.get("id")
    if not user_id:
        return _error(handler, "User ID wajib")
    new_password = _gen_password(12)
    conn = _get_db()
    u = conn.execute("SELECT username FROM users WHERE id=?", (user_id,)).fetchone()
    if not u:
        conn.close()
        return _error(handler, "User tidak ditemukan")
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (_hash_password(new_password), user_id))
    conn.commit()
    conn.close()
    admin = _get_request_user(handler)
    _log_activity(admin["id"], admin["username"], "reset_password", f"Reset password for: {u['username']}")
    _ok(handler, {"username": u["username"], "new_password": new_password, "message": f"Password for {u['username']} reset to: {new_password}"})


# ── Package Handlers ───────────────────────────────────────────────────────

def handle_list_packages(handler):
    conn = _get_db()
    rows = conn.execute("SELECT * FROM packages ORDER BY id").fetchall()
    conn.close()
    _ok(handler, [dict(r) for r in rows])


def handle_create_package(handler, data):
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    name = data.get("name", "").strip()
    slug = data.get("slug", "").strip()
    if not name:
        return _error(handler, "Package name wajib")
    if not slug:
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip("-")
    conn = _get_db()
    existing = conn.execute("SELECT id FROM packages WHERE slug=?", (slug,)).fetchone()
    if existing:
        conn.close()
        return _error(handler, "Package slug sudah digunakan")
    conn.execute("""INSERT INTO packages (name,slug,disk_quota,bandwidth,max_sites,max_databases,max_ftp,max_email,price_monthly,description)
                     VALUES (?,?,?,?,?,?,?,?,?,?)""",
                 (name, slug, data.get("disk_quota", ""), data.get("bandwidth", ""),
                  data.get("max_sites", 0), data.get("max_databases", 0),
                  data.get("max_ftp", 0), data.get("max_email", 0),
                  data.get("price_monthly", 0), data.get("description", "")))
    conn.commit()
    pkg_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    _ok(handler, {"id": pkg_id, "name": name, "slug": slug, "message": f"Package '{name}' created"})


def handle_update_package(handler, data):
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    pkg_id = data.get("id")
    if not pkg_id:
        return _error(handler, "Package ID wajib")
    conn = _get_db()
    fields = []
    values = []
    for key in ["name", "slug", "disk_quota", "bandwidth", "max_sites", "max_databases", "max_ftp", "max_email", "price_monthly", "description"]:
        if key in data:
            fields.append(f"{key}=?")
            values.append(data[key])
    if fields:
        values.append(pkg_id)
        conn.execute(f"UPDATE packages SET {', '.join(fields)} WHERE id=?", values)
        conn.commit()
    conn.close()
    _ok(handler, {"message": "Package updated"})


def handle_delete_package(handler, data):
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    pkg_id = data.get("id")
    if not pkg_id:
        return _error(handler, "Package ID wajib")
    conn = _get_db()
    conn.execute("UPDATE users SET package_id=NULL WHERE package_id=?", (pkg_id,))
    conn.execute("DELETE FROM packages WHERE id=?", (pkg_id,))
    conn.commit()
    conn.close()
    _ok(handler, {"message": "Package deleted"})


# ── Quota & Statistics ─────────────────────────────────────────────────────

def handle_get_quota(handler):
    """Get quota usage for current user."""
    user = _get_request_user(handler)
    if not user:
        # If no user, return server-wide stats
        return _ok(handler, {"disk_used": "0", "disk_limit": "Unlimited", "sites_used": 0, "sites_limit": 0,
                              "databases_used": 0, "databases_limit": 0, "bandwidth_used": "0", "bandwidth_limit": "Unlimited"})
    conn = _get_db()
    u = conn.execute("SELECT package_id FROM users WHERE id=?", (user["id"],)).fetchone()
    pkg = conn.execute("SELECT * FROM packages WHERE id=?", (u["package_id"],)).fetchone() if u["package_id"] else None
    # Count user's resources
    site_domains = [r["domain"] for r in conn.execute("SELECT domain FROM site_owners WHERE user_id=?", (user["id"],)).fetchall()]
    sites_count = len(site_domains)
    # Count databases for user's sites
    db_count = 0
    disk_used_mb = 0
    for domain in site_domains:
        home = _site_home(domain)
        if os.path.isdir(home):
            try:
                out, _, _ = _run(f"du -sm {home} 2>/dev/null | cut -f1", check=False)
                disk_used_mb += int(out) if out.isdigit() else 0
            except:
                pass
        # Count databases
        try:
            db_name = domain.replace(".", "_")[:16]
            out, _, _ = _run(f"mysql -N -e \"SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name LIKE '{db_name}%'\"", check=False)
            db_count += int(out) if out.strip().isdigit() else 0
        except:
            pass
    # Email count
    email_count = conn.execute("SELECT COUNT(*) as c FROM email_accounts WHERE user_id=?", (user["id"],)).fetchone()["c"]
    # FTP count
    ftp_count = conn.execute("SELECT COUNT(*) as c FROM ftp_accounts WHERE user_id=?", (user["id"],)).fetchone()["c"]
    conn.close()
    disk_used_str = f"{disk_used_mb}M" if disk_used_mb < 1024 else f"{disk_used_mb/1024:.1f}G"
    result = {
        "disk_used": disk_used_str,
        "disk_limit": pkg["disk_quota"] if pkg else "Unlimited",
        "sites_used": sites_count,
        "sites_limit": pkg["max_sites"] if pkg else 0,
        "databases_used": db_count,
        "databases_limit": pkg["max_databases"] if pkg else 0,
        "email_used": email_count,
        "email_limit": pkg["max_email"] if pkg else 0,
        "ftp_used": ftp_count,
        "ftp_limit": pkg["max_ftp"] if pkg else 0,
        "bandwidth_used": "0",
        "bandwidth_limit": pkg["bandwidth"] if pkg else "Unlimited",
    }
    _ok(handler, result)


def _check_quota(user_id, resource_type="sites"):
    """Check if user can create more of a resource. Returns (allowed, limit, current)."""
    conn = _get_db()
    u = conn.execute("SELECT package_id FROM users WHERE id=?", (user_id,)).fetchone()
    pkg = conn.execute("SELECT * FROM packages WHERE id=?", (u["package_id"],)).fetchone() if u["package_id"] else None
    if not pkg:
        conn.close()
        return True, 0, 0
    if resource_type == "sites":
        current = conn.execute("SELECT COUNT(*) as c FROM site_owners WHERE user_id=?", (user_id,)).fetchone()["c"]
        limit = pkg["max_sites"]
    elif resource_type == "databases":
        current = 0
        limit = pkg["max_databases"]
    elif resource_type == "email":
        current = conn.execute("SELECT COUNT(*) as c FROM email_accounts WHERE user_id=?", (user_id,)).fetchone()["c"]
        limit = pkg["max_email"]
    elif resource_type == "ftp":
        current = conn.execute("SELECT COUNT(*) as c FROM ftp_accounts WHERE user_id=?", (user_id,)).fetchone()["c"]
        limit = pkg["max_ftp"]
    else:
        current, limit = 0, 0
    conn.close()
    if limit <= 0:
        return True, limit, current
    return current < limit, limit, current


def handle_get_statistics(handler):
    """Get bandwidth/disk statistics per domain."""
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    stats = []
    sites = _get_sites()
    for site in sites:
        home = _site_home(site["domain"])
        disk_size = 0
        if os.path.isdir(home):
            try:
                out, _, _ = _run(f"du -sm {home} 2>/dev/null | cut -f1", check=False)
                disk_size = int(out) if out.strip().isdigit() else 0
            except:
                pass
        # Try to get bandwidth from nginx logs
        bw_rx = 0
        bw_tx = 0
        today = datetime.date.today().isoformat()
        access_log = "%s/%s.access.log" % (CONF["LOG_DIR"], site["domain"])
        if os.path.exists(access_log):
            try:
                out, _, _ = _run(f"awk '{{rx+=$10; tx+=$11}} END {{print rx, tx}}' {access_log} 2>/dev/null", check=False)
                parts = out.split()
                if len(parts) >= 2:
                    bw_rx = int(parts[0])
                    bw_tx = int(parts[1])
            except:
                pass
        stats.append({
            "domain": site["domain"],
            "disk_mb": disk_size,
            "disk_str": f"{disk_size}M" if disk_size < 1024 else f"{disk_size/1024:.1f}G",
            "bandwidth_rx": _fmt_net(bw_rx),
            "bandwidth_tx": _fmt_net(bw_tx),
            "bandwidth_total": _fmt_net(bw_rx + bw_tx),
            "date": today,
        })
    _ok(handler, stats)


def handle_get_activity(handler):
    """Get recent activity log."""
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    conn = _get_db()
    rows = conn.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    activities = [{"id": r["id"], "user_id": r["user_id"], "username": r["username"],
                   "action": r["action"], "details": r["details"], "ip": r["ip"],
                   "created_at": r["created_at"]} for r in rows]
    _ok(handler, activities)


# ── Email Handlers ──────────────────────────────────────────────────────────

def handle_list_email(handler):
    """List email accounts. Admin sees all, customer sees own."""
    user = _get_request_user(handler)
    conn = _get_db()
    if user and user.get("role") == "admin":
        rows = conn.execute("SELECT e.*, u.username as owner FROM email_accounts e LEFT JOIN users u ON e.user_id=u.id ORDER BY e.id").fetchall()
    elif user:
        rows = conn.execute("SELECT * FROM email_accounts WHERE user_id=? ORDER BY id", (user["id"],)).fetchall()
    else:
        rows = []
    conn.close()
    emails = [{"id": r["id"], "domain": r["domain"], "address": r["address"],
               "quota_mb": r["quota_mb"], "user_id": r["user_id"],
               "created_at": r["created_at"],
               "owner": r["owner"] if "owner" in r.keys() else ""} for r in rows]
    _ok(handler, emails)


def handle_create_email(handler, data):
    user = _get_request_user(handler)
    if not user:
        return _error(handler, "Unauthorized", 401)
    domain = _safe_domain(data.get("domain", ""))
    address = data.get("address", "").strip()
    password = data.get("password", "") or _gen_password(10)
    quota_mb = data.get("quota_mb", 500)
    if not domain or not address:
        return _error(handler, "Domain dan address wajib")
    full_address = f"{address}@{domain}"
    # Check quota
    allowed, limit, current = _check_quota(user["id"], "email")
    if not allowed:
        return _error(handler, f"Batas email tercapai ({current}/{limit})")
    conn = _get_db()
    try:
        conn.execute("INSERT INTO email_accounts (domain, address, password, quota_mb, user_id) VALUES (?,?,?,?,?)",
                     (domain, address, _hash_password(password), quota_mb, user["id"]))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return _error(handler, f"Email {full_address} sudah ada")
    conn.close()
    _log_activity(user["id"], user["username"], "create_email", f"Created email: {full_address}")
    # Try to create system email account if postfix/dovecot installed
    try:
        _run(f"adduser --disabled-password --gecos '' {address} 2>/dev/null || true", check=False)
    except:
        pass
    _ok(handler, {"address": full_address, "password": password, "quota_mb": quota_mb, "message": f"Email {full_address} created"})


def handle_delete_email(handler, data):
    user = _get_request_user(handler)
    if not user:
        return _error(handler, "Unauthorized", 401)
    email_id = data.get("id")
    if not email_id:
        return _error(handler, "Email ID wajib")
    conn = _get_db()
    email = conn.execute("SELECT * FROM email_accounts WHERE id=?", (email_id,)).fetchone()
    if not email:
        conn.close()
        return _error(handler, "Email tidak ditemukan")
    if email["user_id"] != user["id"] and user["role"] != "admin":
        conn.close()
        return _error(handler, "Forbidden", 403)
    full_address = f"{email['address']}@{email['domain']}"
    conn.execute("DELETE FROM email_accounts WHERE id=?", (email_id,))
    conn.commit()
    conn.close()
    _log_activity(user["id"], user["username"], "delete_email", f"Deleted email: {full_address}")
    _ok(handler, {"message": f"Email {full_address} deleted"})


# ── FTP Handlers ──────────────────────────────────────────────────────────

def handle_list_ftp(handler):
    user = _get_request_user(handler)
    conn = _get_db()
    if user and user.get("role") == "admin":
        rows = conn.execute("SELECT f.*, u.username as owner FROM ftp_accounts f LEFT JOIN users u ON f.user_id=u.id ORDER BY f.id").fetchall()
    elif user:
        rows = conn.execute("SELECT * FROM ftp_accounts WHERE user_id=? ORDER BY id", (user["id"],)).fetchall()
    else:
        rows = []
    conn.close()
    ftps = [{"id": r["id"], "domain": r["domain"], "username": r["username"],
             "home_dir": r["home_dir"], "user_id": r["user_id"],
             "created_at": r["created_at"],
             "owner": r["owner"] if "owner" in r.keys() else ""} for r in rows]
    _ok(handler, ftps)


def handle_create_ftp(handler, data):
    user = _get_request_user(handler)
    if not user:
        return _error(handler, "Unauthorized", 401)
    domain = _safe_domain(data.get("domain", ""))
    username = data.get("username", "").strip()
    password = data.get("password", "") or _gen_password(12)
    home_dir = data.get("home_dir", "") or _site_home(domain)
    if not domain or not username:
        return _error(handler, "Domain dan username wajib")
    # Check quota
    allowed, limit, current = _check_quota(user["id"], "ftp")
    if not allowed:
        return _error(handler, f"Batas FTP tercapai ({current}/{limit})")
    ftp_user = f"{username}_{domain.replace('.', '_')}"
    conn = _get_db()
    try:
        conn.execute("INSERT INTO ftp_accounts (domain, username, password, home_dir, user_id) VALUES (?,?,?,?,?)",
                     (domain, ftp_user, _hash_password(password), home_dir, user["id"]))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return _error(handler, f"FTP user {ftp_user} sudah ada")
    conn.close()
    _log_activity(user["id"], user["username"], "create_ftp", f"Created FTP: {ftp_user}")
    # Try to create system user
    try:
        _run(f"id {ftp_user} 2>/dev/null || useradd -d {home_dir} -s /usr/sbin/nologin {ftp_user}", check=False)
        if password:
            _run(f"echo '{ftp_user}:{password}' | chpasswd", check=False)
    except:
        pass
    _ok(handler, {"username": ftp_user, "password": password, "home_dir": home_dir, "message": f"FTP user {ftp_user} created"})


def handle_delete_ftp(handler, data):
    user = _get_request_user(handler)
    if not user:
        return _error(handler, "Unauthorized", 401)
    ftp_id = data.get("id")
    if not ftp_id:
        return _error(handler, "FTP ID wajib")
    conn = _get_db()
    ftp = conn.execute("SELECT * FROM ftp_accounts WHERE id=?", (ftp_id,)).fetchone()
    if not ftp:
        conn.close()
        return _error(handler, "FTP tidak ditemukan")
    if ftp["user_id"] != user["id"] and user["role"] != "admin":
        conn.close()
        return _error(handler, "Forbidden", 403)
    ftp_user = ftp["username"]
    conn.execute("DELETE FROM ftp_accounts WHERE id=?", (ftp_id,))
    conn.commit()
    conn.close()
    _log_activity(user["id"], user["username"], "delete_ftp", f"Deleted FTP: {ftp_user}")
    try:
        _run(f"userdel {ftp_user} 2>/dev/null || true", check=False)
    except:
        pass
    _ok(handler, {"message": f"FTP user {ftp_user} deleted"})


# ── App Install Handler ────────────────────────────────────────────────────

def handle_install_app(handler, data):
    """Install apps like Joomla, Laravel, etc."""
    user = _get_request_user(handler)
    if not user:
        return _error(handler, "Unauthorized", 401)
    domain = _safe_domain(data.get("domain", ""))
    app_type = data.get("app_type", "").strip().lower()
    if not domain or not app_type:
        return _error(handler, "Domain dan app type wajib")
    home = _site_home(domain)
    if not os.path.isdir(home):
        return _error(handler, f"Home directory {home} tidak ditemukan")
    try:
        if app_type == "joomla":
            _run(f"cd {home} && wget -q https://downloads.joomla.org/cms/joomla5/5-0-0/Joomla_5-0-0-Stable-Full_Package.tar.gz -O joomla.tar.gz 2>/dev/null")
            _run(f"cd {home} && tar -xzf joomla.tar.gz && rm -f joomla.tar.gz", check=False)
            _ok(handler, {"message": f"Joomla installed for {domain}. Visit https://{domain} to complete setup."})
        elif app_type == "laravel":
            if not os.path.exists("/usr/local/bin/composer"):
                _run("curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer 2>/dev/null || true", check=False)
            _run(f"cd {home} && composer create-project laravel/laravel tmp_laravel 2>/dev/null")
            _run(f"cp -a {home}/tmp_laravel/. {home}/ && rm -rf {home}/tmp_laravel")
            _ok(handler, {"message": f"Laravel installed for {domain}. Run 'php artisan key:generate' to finalize."})
        elif app_type == "wordpress":
            return handle_install_wordpress(handler, data)
        else:
            _error(handler, f"App type '{app_type}' tidak didukung. Gunakan: joomla, laravel, wordpress")
    except Exception as e:
        _error(handler, f"Install gagal: {str(e)}")


# ── Billing Webhook Handler ────────────────────────────────────────────────

def handle_webhook_receive(handler, data):
    """Receive billing webhook events from external billing systems."""
    event_type = data.get("event_type", "").strip()
    payload = json.dumps(data.get("payload", {}))
    if not event_type:
        return _error(handler, "event_type wajib")
    conn = _get_db()
    conn.execute("INSERT INTO webhook_events (event_type, payload, status) VALUES (?,?,?)",
                 (event_type, payload, "received"))
    conn.commit()
    event_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    # Process event
    try:
        if event_type == "payment_confirmed":
            username = data.get("payload", {}).get("username", "")
            pkg_slug = data.get("payload", {}).get("package_slug", "")
            if username and pkg_slug:
                pkg = conn.execute("SELECT id FROM packages WHERE slug=?", (pkg_slug,)).fetchone()
                if pkg:
                    conn.execute("UPDATE users SET status='active', package_id=? WHERE username=?", (pkg["id"], username))
                    conn.commit()
        elif event_type == "payment_expired":
            username = data.get("payload", {}).get("username", "")
            if username:
                conn.execute("UPDATE users SET status='suspended' WHERE username=? AND role='customer'", (username,))
                conn.commit()
        elif event_type == "user_created":
            username = data.get("payload", {}).get("username", "")
            password = data.get("payload", {}).get("password", _gen_password(12))
            email = data.get("payload", {}).get("email", "")
            pkg_slug = data.get("payload", {}).get("package_slug", "")
            if username:
                existing = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
                if not existing:
                    pkg = conn.execute("SELECT id FROM packages WHERE slug=?", (pkg_slug,)).fetchone() if pkg_slug else None
                    conn.execute("INSERT INTO users (username, password_hash, email, role, package_id) VALUES (?,?,?,?,?)",
                                 (username, _hash_password(password), email, "customer", pkg["id"] if pkg else None))
                    conn.commit()
        conn.execute("UPDATE webhook_events SET status='processed' WHERE id=?", (event_id,))
        conn.commit()
    except Exception as e:
        conn.execute("UPDATE webhook_events SET status='failed' WHERE id=?", (event_id,))
        conn.commit()
    conn.close()
    _ok(handler, {"id": event_id, "event_type": event_type, "status": "processed", "message": "Webhook processed"})


def handle_list_webhooks(handler):
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    conn = _get_db()
    rows = conn.execute("SELECT * FROM webhook_events ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    _ok(handler, [dict(r) for r in rows])


# ── App Installer Catalog ────────────────────────────────────────────────────

APPS_CATALOG = [
    {
        "id": "wordpress", "name": "WordPress", "version": "6.7",
        "icon": "WP", "color": "#21759b",
        "description": "Blogger & CMS paling populer di dunia",
        "category": "CMS",
        "website": "https://wordpress.org",
        "fields": [
            {"key": "title", "label": "Site Title", "type": "text", "default": "{domain}", "required": True},
            {"key": "admin_user", "label": "Admin Username", "type": "text", "default": "admin", "required": True},
            {"key": "admin_pass", "label": "Admin Password", "type": "password", "default": "", "required": False},
            {"key": "admin_email", "label": "Admin Email", "type": "text", "default": "admin@{domain}", "required": True},
        ],
    },
    {
        "id": "joomla", "name": "Joomla", "version": "5.0",
        "icon": "J", "color": "#f44321",
        "description": "CMS profesional untuk website kompleks",
        "category": "CMS",
        "website": "https://www.joomla.org",
        "fields": [],
    },
    {
        "id": "laravel", "name": "Laravel", "version": "11.x",
        "icon": "L", "color": "#ff2d20",
        "description": "PHP framework populer untuk web application",
        "category": "Framework",
        "website": "https://laravel.com",
        "fields": [],
    },
    {
        "id": "nextcloud", "name": "Nextcloud", "version": "29",
        "icon": "NC", "color": "#0082c9",
        "description": "Cloud storage pribadi (seperti Google Drive)",
        "category": "Productivity",
        "website": "https://nextcloud.com",
        "fields": [
            {"key": "admin_user", "label": "Admin Username", "type": "text", "default": "admin", "required": True},
            {"key": "admin_pass", "label": "Admin Password", "type": "password", "default": "", "required": False},
            {"key": "admin_email", "label": "Admin Email", "type": "text", "default": "admin@{domain}", "required": True},
        ],
    },
    {
        "id": "prestashop", "name": "PrestaShop", "version": "8.1",
        "icon": "PS", "color": "#df0084",
        "description": "Platform toko online / e-commerce",
        "category": "E-Commerce",
        "website": "https://prestashop.com",
        "fields": [],
    },
    {
        "id": "phpmyadmin", "name": "phpMyAdmin", "version": "5.2",
        "icon": "pMA", "color": "#f0930d",
        "description": "Manage database MySQL via web browser",
        "category": "Database",
        "website": "https://www.phpmyadmin.net",
        "fields": [],
    },
]


def handle_list_apps(handler):
    _ok(handler, APPS_CATALOG)


def handle_install_app(handler, data):
    """Install apps like WordPress, Joomla, Laravel, Nextcloud, etc."""
    user = _get_request_user(handler)
    if not user:
        return _error(handler, "Unauthorized", 401)
    domain = _safe_domain(data.get("domain", ""))
    app_type = data.get("app_type", "").strip().lower()
    if not domain or not app_type:
        return _error(handler, "Domain dan app type wajib")
    home = _site_home(domain)
    wp_dir = "%s/public_html" % home
    if not os.path.isdir(home):
        return _error(handler, "Home directory %s tidak ditemukan. Buat website dulu." % home)

    # Log activity
    _log_activity(user["id"], user["username"], "install_app_start", f"Installing {app_type} on {domain}")

    try:
        if app_type == "wordpress":
            return handle_install_wordpress(handler, data)

        elif app_type == "joomla":
            # Download and extract Joomla
            if not os.path.exists("%s/installation" % wp_dir):
                _run(f"cd /tmp && wget -q https://downloads.joomla.org/cms/joomla5/5-2-4/Joomla_5-2-4-Stable-Full_Package.tar.gz -O joomla.tar.gz 2>/dev/null")
                _run(f"cd {wp_dir} && tar -xzf /tmp/joomla.tar.gz 2>/dev/null")
                _run("rm -f /tmp/joomla.tar.gz", check=False)
            # Create database
            db_name = domain.replace(".", "_")[:16]
            db_pass = _gen_password(16)
            _run(f"mysql -e \"CREATE DATABASE IF NOT EXISTS {db_name}; CREATE USER IF NOT EXISTS '{db_name}'@'localhost' IDENTIFIED BY '{db_pass}'; GRANT ALL ON {db_name}.* TO '{db_name}'@'localhost'; FLUSH PRIVILEGES;\"", check=False)
            _ok(handler, {
                "message": f"Joomla di-extract ke {wp_dir}. Buka https://{domain} untuk lanjutkan instalasi.",
                "database": {"database": db_name, "username": db_name, "password": db_pass, "host": "localhost"},
            })

        elif app_type == "laravel":
            if not os.path.exists("/usr/local/bin/composer"):
                _run("curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer 2>/dev/null || true", check=False)
            # Clear directory first
            _run(f"rm -rf {wp_dir}/* {wp_dir}/.* 2>/dev/null || true", check=False)
            _run(f"cd {home} && composer create-project laravel/laravel public_html 2>/dev/null", timeout=300)
            _run(f"cd {wp_dir} && php artisan key:generate --force 2>/dev/null || true", check=False)
            _ok(handler, {"message": f"Laravel terinstall di {wp_dir}. Framework siap digunakan."})

        elif app_type == "nextcloud":
            nc_ver = "29.0.5"
            tar_url = f"https://download.nextcloud.com/server/releases/nextcloud-{nc_ver}.tar.bz2"
            _run(f"cd {home} && wget -q {tar_url} -O nextcloud.tar.bz2 2>/dev/null", timeout=300)
            _run(f"cd {home} && tar -xjf nextcloud.tar.bz2 2>/dev/null")
            _run(f"cp -a {home}/nextcloud/* {wp_dir}/ && cp -a {home}/nextcloud/.* {wp_dir}/ 2>/dev/null || true")
            _run(f"rm -rf {home}/nextcloud {home}/nextcloud.tar.bz2", check=False)
            # Create data dir
            _run(f"mkdir -p {home}/nextcloud-data", check=False)
            _run(f"chown -R nginx:nginx {wp_dir} {home}/nextcloud-data 2>/dev/null || true", check=False)
            _ok(handler, {"message": f"Nextcloud terinstall. Buka https://{domain} untuk setup awal."})

        elif app_type == "prestashop":
            ps_ver = "8.1.7"
            _run(f"cd {home} && wget -q https://github.com/PrestaShop/PrestaShop/releases/download/{ps_ver}/prestashop_{ps_ver}.zip -O ps.zip 2>/dev/null", timeout=300)
            _run(f"cd {home} && unzip -q ps.zip -d {home}/ 2>/dev/null || true")
            _run(f"cp -a {home}/prestashop/* {wp_dir}/ 2>/dev/null || true")
            _run(f"rm -rf {home}/prestashop {home}/ps.zip {home}/install_prestashop.php 2>/dev/null || true", check=False)
            _run(f"chown -R nginx:nginx {wp_dir} 2>/dev/null || true", check=False)
            _ok(handler, {"message": f"PrestaShop terinstall. Buka https://{domain}/install untuk setup."})

        elif app_type == "phpmyadmin":
            pma_ver = "5.2.1"
            _run(f"cd {home} && wget -q https://files.phpmyadmin.net/phpMyAdmin/{pma_ver}/phpMyAdmin-{pma_ver}-all-languages.tar.gz -O pma.tar.gz 2>/dev/null", timeout=300)
            _run(f"cd {home} && tar -xzf pma.tar.gz 2>/dev/null")
            _run(f"rm -rf {wp_dir}/* 2>/dev/null; cp -a {home}/phpMyAdmin-{pma_ver}/* {wp_dir}/ 2>/dev/null")
            _run(f"rm -rf {home}/phpMyAdmin-{pma_ver} {home}/pma.tar.gz", check=False)
            # Create config
            _run(f"cp {wp_dir}/config.sample.inc.php {wp_dir}/config.inc.php 2>/dev/null || true", check=False)
            _run(f"sed -i \"s/.*blowfish_secret.*/\\$cfg\\['blowfish_secret'] = '{_gen_password(32)}';/\" {wp_dir}/config.inc.php 2>/dev/null || true", check=False)
            _ok(handler, {"message": f"phpMyAdmin terinstall. Buka https://{domain} untuk akses database."})

        else:
            _error(handler, f"App type '{app_type}' tidak didukung. Pilihan: wordpress, joomla, laravel, nextcloud, prestashop, phpmyadmin")

    except Exception as e:
        _log_activity(user["id"], user["username"], "install_app_error", f"Failed {app_type} on {domain}: {str(e)}")
        _error(handler, f"Install gagal: {str(e)}")


# ── Server Management Handlers (from v2.1) ──────────────────────────────────

def handle_health(handler):
    _ok(handler, {"status": "ok", "version": "3.0"})


def handle_server_info(handler):
    try:
        mem = _run("free -m | grep Mem")[0].split()
        mem_total, mem_used, mem_free = mem[1], mem[2], mem[3]
        disk = _run("df -h / | tail -1")[0].split()
        disk_total, disk_used, disk_free = disk[1], disk[2], disk[3]
        cpu_stat = _run("grep 'cpu ' /proc/stat")[0].split()
        cpu_idle_1 = int(cpu_stat[4])
        time.sleep(0.1)
        cpu_stat = _run("grep 'cpu ' /proc/stat")[0].split()
        cpu_idle_2 = int(cpu_stat[4])
        cpu_total = sum(int(x) for x in cpu_stat[1:])
        cpu_pct = round((1 - (cpu_idle_2 - cpu_idle_1) / max(cpu_total - sum(int(x) for x in _run("grep 'cpu ' /proc/stat")[0].split()[1:]) + (cpu_idle_1 - cpu_idle_1), 1)) * 100, 1)
        # Simplified CPU calculation
        try:
            out = _run("top -bn1 | grep 'Cpu' | awk '{print $2}'")[0]
            cpu_pct = round(float(out.replace(',', '.')), 1)
        except:
            cpu_pct = 0
        cpu_cores = _run("nproc")[0]
        uptime = _run("uptime -p 2>/dev/null || uptime")[0].strip()
        load = _run("cat /proc/loadavg")[0].split()[:3]
        # Network
        rx_bytes, tx_bytes = 0, 0
        try:
            net = _run("cat /proc/net/dev | tail -2 | head -1")[0].split()
            rx_bytes = net[1]
            tx_bytes = net[9]
        except:
            pass
        os_info = "%s %s" % (platform.system(), platform.release())
        hostname = platform.node()
        kernel = platform.release()
        server_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sites = _get_sites()
        # User count
        conn = _get_db()
        user_count = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        conn.close()
        _ok(handler, {
            "memory_total": mem_total, "memory_used": mem_used, "memory_free": mem_free,
            "disk_total": disk_total, "disk_used": disk_used, "disk_free": disk_free,
            "cpu_percent": cpu_pct, "cpu_cores": cpu_cores, "uptime": uptime,
            "cpu_load_1m": float(load[0]), "cpu_load_5m": float(load[1]), "cpu_load_15m": float(load[2]),
            "net_rx_total": _fmt_net(rx_bytes), "net_tx_total": _fmt_net(tx_bytes),
            "os": os_info, "kernel": kernel, "hostname": hostname, "server_time": server_time,
            "total_sites": len(sites), "active_sites": len([s for s in sites if s.get("exists")]),
            "total_users": user_count,
        })
    except Exception as e:
        _error(handler, str(e))


def handle_list_sites(handler):
    """List sites. Admin sees all, customer sees own."""
    user = _get_request_user(handler)
    if user and user.get("role") != "admin":
        sites = _get_user_sites(user["id"])
    else:
        sites = _get_sites()
    _ok(handler, sites)


def handle_create_site(handler, data):
    user = _get_request_user(handler)
    is_admin = user and user.get("role") == "admin"
    if not user:
        return _error(handler, "Unauthorized", 401)
    domain = _safe_domain(data.get("domain", ""))
    owner = data.get("owner", domain.split(".")[0])
    pkg = data.get("package", "")
    email = data.get("email", "")
    if not domain:
        return _error(handler, "Domain wajib diisi")
    # Check quota for customer
    if not is_admin:
        allowed, limit, current = _check_quota(user["id"], "sites")
        if not allowed:
            return _error(handler, f"Batas situs tercapai ({current}/{limit}). Upgrade package Anda.")
    home = _site_home(domain)
    nginx_conf = _site_nginx(domain)
    if os.path.exists(nginx_conf):
        return _error(handler, f"Situs {domain} sudah ada")
    try:
        # Create home directory
        os.makedirs(home, exist_ok=True)
        os.makedirs("%s/public_html" % home, exist_ok=True)
        # Create default welcome page
        welcome_html = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Selamat Datang - %(domain)s</title>
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
<p class="domain">%(domain)s</p>
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
<span class="card-value">/home/%(domain)s/public_html</span>
</div>
</div>
<div class="actions">
<a href="#" class="btn btn-primary">Login ke Panel</a>
<a href="#" class="btn btn-secondary">Upload File Anda</a>
</div>
<p class="footer">Dikelola oleh <a href="https://github.com/ropick/zaydpanel" target="_blank">ZaydPanel</a> &mdash; Free &amp; Open Source Hosting Control Panel</p>
</div>
</body>
</html>""" % {"domain": domain}
        with open("%s/public_html/index.html" % home, "w") as f:
            f.write(welcome_html)
        # Create nginx config
        nginx_tmpl = """server {
    listen 80;
    server_name %s www.%s;
    root %s/public_html;
    index index.php index.html;
    access_log /var/log/nginx/%s.access.log;
    error_log /var/log/nginx/%s.error.log;
    location / {
        try_files $uri $uri/ =404;
    }
    location ~ \\.php$ {
        fastcgi_pass unix:/run/php-fpm/www.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
}""" % (domain, domain, home, domain, domain)
        with open(nginx_conf, "w") as f:
            f.write(nginx_tmpl)
        # Create PHP-FPM pool
        pool_conf = """[%s]
user = nginx
group = nginx
listen = /run/php-fpm/%s.sock
listen.owner = nginx
listen.group = nginx
pm = dynamic
pm.max_children = 5
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 3
pm.max_requests = 500
php_admin_value[open_basedir] = %s:/tmp
""" % (domain, domain, home)
        pool_path = "%s/%s.conf" % (CONF["PHP_FPM_CONF_DIR"], domain)
        with open(pool_path, "w") as f:
            f.write(pool_conf)
        # Restart services
        _run("nginx -t 2>/dev/null && systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null", check=False)
        _run("systemctl restart php-fpm 2>/dev/null || systemctl reload php-fpm 2>/dev/null", check=False)
        # Create database
        db_name = domain.replace(".", "_")[:16]
        db_pass = _gen_password(16)
        try:
            _run(f"mysql -e \"CREATE DATABASE IF NOT EXISTS {db_name}; CREATE USER IF NOT EXISTS '{db_name}'@'localhost' IDENTIFIED BY '{db_pass}'; GRANT ALL ON {db_name}.* TO '{db_name}'@'localhost'; FLUSH PRIVILEGES;\"")
        except:
            db_pass = ""
        # Assign site to user in DB
        conn = _get_db()
        target_user_id = user["id"] if not is_admin else None
        if is_admin:
            target_user = conn.execute("SELECT id FROM users WHERE username=?", (owner,)).fetchone()
            target_user_id = target_user["id"] if target_user else None
        if target_user_id:
            try:
                conn.execute("INSERT INTO site_owners (domain, user_id) VALUES (?,?)", (domain, target_user_id))
                conn.commit()
            except sqlite3.IntegrityError:
                pass
        conn.close()
        admin_user = _get_request_user(handler)
        _log_activity(admin_user["id"] if admin_user else 0, admin_user["username"] if admin_user else "",
                       "create_site", f"Created site: {domain}")
        result = {
            "domain": domain, "username": owner, "home_dir": home,
        }
        if db_pass:
            result["database"] = {"database": db_name, "username": db_name, "password": db_pass, "host": "localhost"}
        _ok(handler, result)
    except Exception as e:
        _error(handler, str(e))


def handle_delete_site(handler, data):
    user = _get_request_user(handler)
    if not user or user.get("role") != "admin":
        return _error(handler, "Admin only", 403)
    domain = _safe_domain(data.get("domain", ""))
    if not domain:
        return _error(handler, "Domain wajib")
    try:
        home = _site_home(domain)
        nginx_conf = _site_nginx(domain)
        pool_conf = "%s/%s.conf" % (CONF["PHP_FPM_CONF_DIR"], domain)
        # Remove nginx config
        if os.path.exists(nginx_conf):
            os.remove(nginx_conf)
        # Remove pool
        if os.path.exists(pool_conf):
            os.remove(pool_conf)
        # Remove home dir
        if os.path.isdir(home):
            shutil.rmtree(home)
        # Remove database
        db_name = domain.replace(".", "_")[:16]
        _run(f"mysql -e \"DROP DATABASE IF EXISTS {db_name}; DROP USER IF EXISTS '{db_name}'@'localhost'; FLUSH PRIVILEGES;\"", check=False)
        # Remove from DB
        conn = _get_db()
        conn.execute("DELETE FROM site_owners WHERE domain=?", (domain,))
        conn.commit()
        conn.close()
        _run("nginx -t 2>/dev/null && systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null", check=False)
        _run("systemctl restart php-fpm 2>/dev/null || systemctl reload php-fpm 2>/dev/null", check=False)
        admin_user = _get_request_user(handler)
        _log_activity(admin_user["id"], admin_user["username"], "delete_site", f"Deleted site: {domain}")
        _ok(handler, {"message": f"Site {domain} deleted"})
    except Exception as e:
        _error(handler, str(e))


def _generate_wp_salt(length=64):
    """Generate random salt strings for WordPress wp-config.php."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    return "".join(secrets.choice(chars) for _ in range(length))


def _generate_wp_config(db_name, db_user, db_pass, db_host="localhost"):
    """Generate a complete wp-config.php content."""
    salts = {key: _generate_wp_salt() for key in [
        "AUTH_KEY", "SECURE_AUTH_KEY", "LOGGED_IN_KEY", "NONCE_KEY",
        "AUTH_SALT", "SECURE_AUTH_SALT", "LOGGED_IN_SALT", "NONCE_SALT",
    ]}
    return f"""<?php
/**
 * WordPress Configuration - Generated by ZaydPanel
 */

// Database settings
define('DB_NAME', '{db_name}');
define('DB_USER', '{db_user}');
define('DB_PASSWORD', '{db_pass}');
define('DB_HOST', '{db_host}');
define('DB_CHARSET', 'utf8mb4');
define('DB_COLLATE', '');

// Authentication unique keys and salts
{chr(10).join(f"define('{k}', '{v}');" for k, v in salts.items())}

// WordPress database table prefix
$table_prefix = 'wp_';

// Debugging (disable in production)
define('WP_DEBUG', false);
define('WP_DEBUG_LOG', false);
define('WP_DEBUG_DISPLAY', false);

// Performance
define('WP_MEMORY_LIMIT', '256M');
define('WP_MAX_MEMORY_LIMIT', '512M');
define('DISALLOW_FILE_EDIT', true);
define('WP_AUTO_UPDATE_CORE', 'minor');
define('FS_METHOD', 'direct');

// Security
define('WP_HTTP_BLOCK_EXTERNAL', true);
define('WP_ACCESSIBLE_HOSTS', 'api.wordpress.org,downloads.wordpress.org');

// Path & URL
if (isset($_SERVER['HTTP_HOST'])) {{
    define('WP_HOME', 'https://' . $_SERVER['HTTP_HOST']);
    define('WP_SITEURL', 'https://' . $_SERVER['HTTP_HOST']);
}}

/* That's all, stop editing! */
if ( ! defined('ABSPATH') ) {{
    define('ABSPATH', __DIR__ . '/');
}}
require_once ABSPATH . 'wp-settings.php';
"""


def handle_install_wordpress(handler, data):
    """Install WordPress with full setup: download, wp-config, DB, permissions."""
    user = _get_request_user(handler)
    if not user:
        return _error(handler, "Unauthorized", 401)
    domain = _safe_domain(data.get("domain", ""))
    title = data.get("title", domain)
    admin_user = data.get("admin_user", "admin")
    admin_pass = data.get("admin_pass", "") or _gen_password(12)
    admin_email = data.get("admin_email", f"{admin_user}@{domain}")
    home = _site_home(domain)
    wp_dir = "%s/public_html" % home
    if not os.path.isdir(wp_dir):
        return _error(handler, f"Home directory {wp_dir} tidak ditemukan. Buat website dulu.")
    if os.path.exists("%s/wp-login.php" % wp_dir):
        return _error(handler, "WordPress sudah terinstall di domain ini. Hapus dulu atau gunakan domain lain.")
    try:
        # Step 1: Download & extract WordPress
        _log_activity(user["id"], user["username"], "install_wordpress", f"Downloading WordPress for {domain}")
        _run(f"cd {wp_dir} && wget -q --timeout=120 https://wordpress.org/latest.tar.gz -O /tmp/wp-latest.tar.gz && tar -xzf /tmp/wp-latest.tar.gz && mv wordpress/* . && mv wordpress/.* . 2>/dev/null; rm -rf wordpress /tmp/wp-latest.tar.gz")
        if not os.path.exists("%s/wp-settings.php" % wp_dir):
            return _error(handler, "Gagal mengekstrak WordPress. Coba lagi.")

        # Step 2: Create database
        db_name = domain.replace(".", "_")[:16]
        db_pass = _gen_password(16)
        _run(f"mysql -e \"CREATE DATABASE IF NOT EXISTS \\`{db_name}\\`; CREATE USER IF NOT EXISTS '{db_name}'@'localhost' IDENTIFIED BY '{db_pass}'; GRANT ALL ON \\`{db_name}\\`.* TO '{db_name}'@'localhost'; FLUSH PRIVILEGES;\"", check=False)

        # Step 3: Generate wp-config.php
        wp_config = _generate_wp_config(db_name, db_name, db_pass)
        config_path = "%s/wp-config.php" % wp_dir
        # Backup sample config if exists
        if os.path.exists("%s/wp-config-sample.php" % wp_dir):
            os.rename("%s/wp-config-sample.php" % wp_dir, "%s/wp-config-sample.php.bak" % wp_dir)
        with open(config_path, "w") as f:
            f.write(wp_config)

        # Step 4: Fix permissions
        _run(f"chown -R nginx:nginx {wp_dir}", check=False)
        _run(f"chmod 640 {config_path}", check=False)
        _run(f"find {wp_dir} -type d -exec chmod 755 {{}} \\;", check=False)
        _run(f"find {wp_dir} -type f -exec chmod 644 {{}} \\;", check=False)

        # Step 5: Try WP-CLI core install (if available)
        wp_cli = shutil.which("wp")
        if wp_cli:
            _run(f"cd {wp_dir} && wp core install --url=https://{domain} --title='{title}' --admin_user={admin_user} --admin_password='{admin_pass}' --admin_email='{admin_email}' --allow-root 2>/dev/null", check=False)
            _run(f"cd {wp_dir} && wp rewrite structure '/%postname%/' --allow-root 2>/dev/null", check=False)
            _run(f"cd {wp_dir} && wp plugin delete hello akismet --allow-root 2>/dev/null", check=False)
            _log_activity(user["id"], user["username"], "install_wordpress", f"WordPress fully installed on {domain} via WP-CLI")
        else:
            _log_activity(user["id"], user["username"], "install_wordpress", f"WordPress files+config installed on {domain} (manual setup via web)")

        # Restart PHP-FPM to pick up new site
        _run("systemctl restart php-fpm 2>/dev/null || systemctl restart php8.3-fpm 2>/dev/null || true", check=False)

        _ok(handler, {
            "message": f"WordPress terinstall di {domain}!",
            "site_url": f"https://{domain}",
            "admin_url": f"https://{domain}/wp-admin",
            "admin_user": admin_user,
            "admin_pass": admin_pass,
            "admin_email": admin_email,
            "wp_cli": bool(wp_cli),
            "needs_web_setup": not bool(wp_cli),
            "database": {"database": db_name, "username": db_name, "password": db_pass, "host": "localhost"},
        })
    except Exception as e:
        _error(handler, f"Gagal install WordPress: {str(e)}")


def handle_remove_wordpress(handler, data):
    """Remove WordPress installation from a domain."""
    user = _get_request_user(handler)
    if not user:
        return _error(handler, "Unauthorized", 401)
    domain = _safe_domain(data.get("domain", ""))
    if not domain:
        return _error(handler, "Domain wajib")
    home = _site_home(domain)
    wp_dir = "%s/public_html" % home
    if not os.path.exists("%s/wp-login.php" % wp_dir):
        return _error(handler, "WordPress tidak ditemukan di domain ini.")
    try:
        # Remove all WordPress files
        _run(f"rm -rf {wp_dir}/* {wp_dir}/.* 2>/dev/null || true", check=False)
        # Optionally remove database
        drop_db = data.get("drop_database", False)
        if drop_db:
            db_name = domain.replace(".", "_")[:16]
            _run(f"mysql -e \"DROP DATABASE IF EXISTS \\`{db_name}\\`; DROP USER IF EXISTS '{db_name}'@'localhost'; FLUSH PRIVILEGES;\"", check=False)
        # Recreate public_html
        os.makedirs(wp_dir, exist_ok=True)
        _run(f"chown -R nginx:nginx {wp_dir}", check=False)
        _log_activity(user["id"], user["username"], "remove_wordpress", f"Removed WordPress from {domain}")
        _ok(handler, {"message": f"WordPress berhasil dihapus dari {domain}", "database_dropped": drop_db})
    except Exception as e:
        _error(handler, str(e))


def handle_processes(handler):
    try:
        out = _run("ps aux --sort=-%%cpu | head -21")[0]
        lines = out.strip().split("\n")[1:]
        procs = []
        for line in lines:
            parts = line.split(None, 10)
            if len(parts) < 11:
                continue
            try:
                procs.append({"pid": int(parts[1]), "user": parts[0], "cpu": float(parts[2]), "mem": float(parts[3]), "command": parts[10][:200]})
            except:
                pass
        _ok(handler, procs)
    except Exception as e:
        _error(handler, str(e))


def handle_list_databases(handler):
    try:
        out, _, _ = _run("mysql -N -e \"SELECT table_schema, ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb FROM information_schema.tables WHERE table_schema NOT IN ('mysql','information_schema','performance_schema','sys') GROUP BY table_schema ORDER BY table_schema\"", check=False)
        databases = []
        for line in out.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                name = parts[0].strip()
                size = parts[1].strip()
                domain = name.replace("_", ".")
                databases.append({"name": name, "user": name, "size": f"{size} MB", "domain": domain})
        _ok(handler, databases)
    except Exception as e:
        _error(handler, str(e))


def handle_create_database(handler, data):
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    domain = _safe_domain(data.get("domain", ""))
    db_name = domain.replace(".", "_")[:16]
    db_pass = _gen_password(16)
    try:
        _run(f"mysql -e \"CREATE DATABASE IF NOT EXISTS {db_name}; CREATE USER IF NOT EXISTS '{db_name}'@'localhost' IDENTIFIED BY '{db_pass}'; GRANT ALL ON {db_name}.* TO '{db_name}'@'localhost'; FLUSH PRIVILEGES;\"")
        _ok(handler, {"database": db_name, "username": db_name, "password": db_pass, "host": "localhost", "message": f"Database {db_name} created"})
    except Exception as e:
        _error(handler, str(e))


def handle_delete_database(handler, data):
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    name = data.get("database", "")
    if not name:
        return _error(handler, "Database name wajib")
    try:
        _run(f"mysql -e \"DROP DATABASE IF EXISTS {name}; DROP USER IF EXISTS '{name}'@'localhost'; FLUSH PRIVILEGES;\"")
        _ok(handler, {"message": f"Database {name} deleted"})
    except Exception as e:
        _error(handler, str(e))


def handle_list_ssl(handler):
    certs = []
    sites = _get_sites()
    for site in sites:
        if site.get("ssl"):
            cert_path = "/etc/letsencrypt/live/%s/cert.pem" % site["domain"]
            if os.path.exists(cert_path):
                try:
                    out, _, _ = _run(f"openssl x509 -in {cert_path} -noout -dates -issuer 2>/dev/null", check=False)
                    lines = out.strip().split("\n")
                    expires = ""
                    issuer = ""
                    for l in lines:
                        if l.startswith("notAfter="):
                            expires = l.replace("notAfter=", "")
                        if l.startswith("issuer="):
                            issuer = l.replace("issuer=", "")
                    if expires:
                        from email.utils import parsedate_to_datetime
                        try:
                            exp_date = parsedate_to_datetime(expires)
                            days_left = (exp_date - datetime.datetime.now(exp_date.tzinfo)).days
                        except:
                            days_left = 0
                    else:
                        days_left = 0
                    certs.append({"domain": site["domain"], "issuer": issuer, "expires_at": expires, "days_left": max(days_left, 0), "type": "Let's Encrypt"})
                except:
                    certs.append({"domain": site["domain"], "issuer": "Unknown", "expires_at": "Unknown", "days_left": 0, "type": "SSL"})
    _ok(handler, certs)


def handle_issue_ssl(handler, data):
    user = _get_request_user(handler)
    if not user:
        return _error(handler, "Unauthorized", 401)
    domain = _safe_domain(data.get("domain", ""))
    if not domain:
        return _error(handler, "Domain wajib")
    try:
        _run(f"certbot --nginx -d {domain} --non-interactive --agree-tos --email admin@{domain} 2>&1", check=False)
        _run("systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null", check=False)
        _log_activity(user["id"], user["username"], "issue_ssl", f"SSL issued for {domain}")
        _ok(handler, {"message": f"SSL certificate issued for {domain}"})
    except Exception as e:
        _error(handler, f"SSL issue failed: {str(e)}")


def handle_renew_ssl(handler, data):
    domain = _safe_domain(data.get("domain", ""))
    try:
        _run(f"certbot renew --cert-name {domain} --non-interactive 2>&1", check=False)
        _run("systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null", check=False)
        _ok(handler, {"message": f"SSL renewed for {domain}"})
    except Exception as e:
        _error(handler, str(e))


def handle_get_logs(handler, domain, log_type, query=None):
    domain = _safe_domain(domain)
    log_file = "%s/%s.%s.log" % (CONF["LOG_DIR"], domain, log_type)
    if not os.path.exists(log_file):
        return _ok(handler, {"logs": [], "domain": domain, "type": log_type})
    lines = int(query.get("lines", "100")) if query else 100
    try:
        out, _, _ = _run(f"tail -n {lines} {log_file}", check=False)
        logs = []
        for line in out.strip().split("\n"):
            if line.strip():
                logs.append({"timestamp": "", "level": "info", "message": line.strip()})
        _ok(handler, {"logs": logs, "domain": domain, "type": log_type})
    except Exception as e:
        _error(handler, str(e))


def handle_list_files(handler, domain, path="/"):
    domain = _safe_domain(domain)
    home = _site_home(domain)
    target = os.path.normpath(os.path.join(home, path.lstrip("/")))
    if not target.startswith(home):
        return _error(handler, "Path traversal detected")
    if not os.path.isdir(target):
        return _error(handler, "Directory not found")
    entries = []
    try:
        for entry in sorted(os.listdir(target)):
            full = os.path.join(target, entry)
            try:
                st = os.stat(full)
                entries.append({
                    "name": entry,
                    "path": os.path.join(path, entry) if path != "/" else "/%s" % entry,
                    "type": "dir" if os.path.isdir(full) else "file",
                    "size": st.st_size,
                    "modified": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "permissions": oct(st.st_mode)[-3:],
                })
            except:
                pass
    except PermissionError:
        return _error(handler, "Permission denied")
    _ok(handler, {"files": entries, "path": path})


def handle_read_file(handler, domain, path):
    domain = _safe_domain(domain)
    home = _site_home(domain)
    target = os.path.normpath(os.path.join(home, path.lstrip("/")))
    if not target.startswith(home):
        return _error(handler, "Path traversal detected")
    try:
        with open(target, "r", errors="replace") as f:
            content = f.read()
        _ok(handler, {"content": content, "size": os.path.getsize(target)})
    except Exception as e:
        _error(handler, str(e))


def handle_save_file(handler, domain, path, data):
    domain = _safe_domain(domain)
    home = _site_home(domain)
    target = os.path.normpath(os.path.join(home, path.lstrip("/")))
    if not target.startswith(home):
        return _error(handler, "Path traversal detected")
    try:
        with open(target, "w") as f:
            f.write(data.get("content", ""))
        _ok(handler, {"message": "File saved"})
    except Exception as e:
        _error(handler, str(e))


def handle_delete_file(handler, domain, path):
    domain = _safe_domain(domain)
    home = _site_home(domain)
    target = os.path.normpath(os.path.join(home, path.lstrip("/")))
    if not target.startswith(home):
        return _error(handler, "Path traversal detected")
    try:
        if os.path.isfile(target):
            os.remove(target)
        elif os.path.isdir(target):
            shutil.rmtree(target)
        _ok(handler, {"message": "Deleted"})
    except Exception as e:
        _error(handler, str(e))


def handle_upload_file(handler, domain, path, data):
    domain = _safe_domain(domain)
    home = _site_home(domain)
    target = os.path.normpath(os.path.join(home, path.lstrip("/")))
    if not target.startswith(home):
        return _error(handler, "Path traversal detected")
    try:
        content_b64 = data.get("content_b64", "")
        content = base64.b64decode(content_b64)
        with open(target, "wb") as f:
            f.write(content)
        _ok(handler, {"message": "File uploaded", "size": len(content)})
    except Exception as e:
        _error(handler, str(e))


def handle_mkdir(handler, domain, path):
    domain = _safe_domain(domain)
    home = _site_home(domain)
    target = os.path.normpath(os.path.join(home, path.lstrip("/")))
    if not target.startswith(home):
        return _error(handler, "Path traversal detected")
    try:
        os.makedirs(target, exist_ok=True)
        _ok(handler, {"message": "Directory created"})
    except Exception as e:
        _error(handler, str(e))


def handle_rename_file(handler, data):
    domain = _safe_domain(data.get("domain", ""))
    home = _site_home(domain)
    old_path = os.path.normpath(os.path.join(home, data.get("old_path", "").lstrip("/")))
    new_path = os.path.normpath(os.path.join(home, data.get("new_path", "").lstrip("/")))
    if not old_path.startswith(home) or not new_path.startswith(home):
        return _error(handler, "Path traversal detected")
    try:
        os.rename(old_path, new_path)
        _ok(handler, {"message": "Renamed"})
    except Exception as e:
        _error(handler, str(e))


def handle_list_cron(handler):
    try:
        entries = []
        if os.path.exists(CONF["CRON_DIR"]):
            for f in sorted(Path(CONF["CRON_DIR"]).glob("*.json")):
                try:
                    with open(f) as fh:
                        job = json.load(fh)
                        job["id"] = f.stem
                        entries.append(job)
                except:
                    pass
        _ok(handler, entries)
    except Exception as e:
        _error(handler, str(e))


def handle_create_cron(handler, data):
    os.makedirs(CONF["CRON_DIR"], exist_ok=True)
    domain = data.get("domain", "")
    schedule = data.get("schedule", "")
    command = data.get("command", "")
    description = data.get("description", "")
    if not domain or not schedule or not command:
        return _error(handler, "domain, schedule, command wajib")
    job_id = "%s_%d" % (domain.replace(".", "_"), int(time.time()))
    job = {"domain": domain, "schedule": schedule, "command": command, "description": description, "enabled": True}
    with open("%s/%s.json" % (CONF["CRON_DIR"], job_id), "w") as f:
        json.dump(job, f)
    _ok(handler, {"id": job_id, **job})


def handle_delete_cron(handler, data):
    job_id = data.get("id", "")
    if not job_id:
        return _error(handler, "Job ID wajib")
    fpath = "%s/%s.json" % (CONF["CRON_DIR"], job_id)
    if os.path.exists(fpath):
        os.remove(fpath)
    _ok(handler, {"message": "Cron job deleted"})


def handle_toggle_cron(handler, data):
    job_id = data.get("id", "")
    enabled = data.get("enabled", True)
    fpath = "%s/%s.json" % (CONF["CRON_DIR"], job_id)
    if os.path.exists(fpath):
        try:
            with open(fpath) as f:
                job = json.load(f)
            job["enabled"] = enabled
            with open(fpath, "w") as f:
                json.dump(job, f)
        except:
            pass
    _ok(handler, {"message": "Cron job toggled"})


def handle_list_backups(handler):
    backups = []
    if os.path.exists(CONF["BACKUP_DIR"]):
        for f in sorted(Path(CONF["BACKUP_DIR"]).glob("*.tar.gz")):
            stat = f.stat()
            domain = f.stem.split("_")[0] if "_" in f.stem else f.stem.replace(".tar", "")
            backups.append({
                "id": f.stem, "domain": domain, "filename": f.name,
                "size": _fmt_net(stat.st_size), "created_at": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "type": "full",
            })
    _ok(handler, backups)


def handle_create_backup(handler, data):
    domain = _safe_domain(data.get("domain", ""))
    home = _site_home(domain)
    if not os.path.isdir(home):
        return _error(handler, f"Home directory {home} tidak ditemukan")
    os.makedirs(CONF["BACKUP_DIR"], exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{domain}_{ts}.tar.gz"
    filepath = "%s/%s" % (CONF["BACKUP_DIR"], filename)
    try:
        _run(f"tar -czf {filepath} -C {os.path.dirname(home)} {os.path.basename(home)} 2>/dev/null")
        _ok(handler, {"id": domain + "_" + ts, "domain": domain, "filename": filename, "size": _fmt_net(os.path.getsize(filepath)), "message": "Backup created"})
    except Exception as e:
        _error(handler, str(e))


def handle_restore_backup(handler, data):
    backup_id = data.get("id", "")
    filepath = "%s/%s.tar.gz" % (CONF["BACKUP_DIR"], backup_id)
    if not os.path.exists(filepath):
        return _error(handler, "Backup tidak ditemukan")
    try:
        domain = backup_id.split("_")[0]
        home = _site_home(domain)
        if os.path.isdir(home):
            shutil.rmtree(home)
        os.makedirs(os.path.dirname(home), exist_ok=True)
        _run(f"tar -xzf {filepath} -C {os.path.dirname(home)}")
        _ok(handler, {"message": f"Backup {backup_id} restored"})
    except Exception as e:
        _error(handler, str(e))


def handle_delete_backup(handler, data):
    backup_id = data.get("id", "")
    filepath = "%s/%s.tar.gz" % (CONF["BACKUP_DIR"], backup_id)
    if os.path.exists(filepath):
        os.remove(filepath)
    _ok(handler, {"message": "Backup deleted"})


def handle_list_php_versions(handler):
    versions = []
    try:
        out, _, _ = _run("ls /etc/php-fpm.d/ 2>/dev/null || ls /etc/php/*/fpm/ 2>/dev/null", check=False)
    except:
        out = ""
    try:
        active_ver = _run("php -v | head -1 | awk '{print $2}'")[0]
    except:
        active_ver = CONF["PHP_VERSION"]
    versions.append({"version": active_ver, "path": "/usr/bin/php", "active": True})
    _ok(handler, versions)


def handle_set_php_version(handler, data):
    domain = _safe_domain(data.get("domain", ""))
    version = data.get("version", "")
    if not domain or not version:
        return _error(handler, "Domain dan version wajib")
    try:
        nginx_conf = _site_nginx(domain)
        if os.path.exists(nginx_conf):
            content = Path(nginx_conf).read_text()
            content = re.sub(r'fastcgi_pass.*?;', f'fastcgi_pass unix:/run/php-fpm/{domain}.sock;', content)
            Path(nginx_conf).write_text(content)
        _run("systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null", check=False)
        _ok(handler, {"message": f"PHP version for {domain} set to {version}"})
    except Exception as e:
        _error(handler, str(e))


def handle_get_settings(handler):
    settings = [
        {"key": "php_version", "value": CONF["PHP_VERSION"], "description": "Default PHP Version"},
        {"key": "agent_version", "value": "3.0", "description": "Agent Version"},
        {"key": "sites_dir", "value": CONF["SITES_DIR"], "description": "Sites Home Directory"},
        {"key": "backup_dir", "value": CONF["BACKUP_DIR"], "description": "Backup Directory"},
    ]
    _ok(handler, settings)


def handle_update_setting(handler, data):
    key = data.get("key", "")
    value = data.get("value", "")
    if key == "php_version":
        CONF["PHP_VERSION"] = value
    _ok(handler, {"message": f"Setting {key} updated to {value}"})


def handle_restart_service(handler, data):
    if not _is_admin(handler):
        return _error(handler, "Admin only", 403)
    service = data.get("service", "")
    if not service:
        return _error(handler, "Service name wajib")
    try:
        _run(f"systemctl restart {service}")
        _ok(handler, {"message": f"Service {service} restarted"})
    except Exception as e:
        _error(handler, str(e))


# ── HTTP Server ────────────────────────────────────────────────────────────

class AgentHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-User-Token")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        try:
            if path == "/health": return handle_health(self)
            if path == "/server-info": return handle_server_info(self)
            if path == "/processes": return handle_processes(self)
            if path == "/sites": return handle_list_sites(self)
            if path == "/ssl/list": return handle_list_ssl(self)
            if path == "/db/list": return handle_list_databases(self)
            if path == "/cron/list": return handle_list_cron(self)
            if path == "/backup/list": return handle_list_backups(self)
            if path == "/php/versions": return handle_list_php_versions(self)
            if path == "/settings": return handle_get_settings(self)
            if path == "/auth/me": return handle_auth_me(self)
            if path == "/users": return handle_list_users(self)
            if path == "/packages": return handle_list_packages(self)
            if path == "/email/list": return handle_list_email(self)
            if path == "/ftp/list": return handle_list_ftp(self)
            if path == "/quota": return handle_get_quota(self)
            if path == "/statistics": return handle_get_statistics(self)
            if path == "/activity": return handle_get_activity(self)
            if path == "/webhooks": return handle_list_webhooks(self)
            if path == "/apps": return handle_list_apps(self)
            if path.startswith("/files/"):
                parts = path[7:].split("/", 1)
                domain = parts[0]
                filepath = "/" + parts[1] if len(parts) > 1 else "/"
                return handle_list_files(self, domain, filepath)
            if path.startswith("/file-content/"):
                parts = path[14:].split("/", 1)
                domain = parts[0]
                filepath = "/" + parts[1] if len(parts) > 1 else "/"
                return handle_read_file(self, domain, filepath)
            if path.startswith("/logs/") and path.count("/") >= 3:
                parts = path[6:].split("/", 2)
                domain, log_type = parts[0], parts[1]
                query_str = parts[2] if len(parts) > 2 else ""
                query = {}
                if query_str:
                    for kv in query_str.split("&"):
                        if "=" in kv:
                            query[kv.split("=")[0]] = kv.split("=", 1)[1]
                return handle_get_logs(self, domain, log_type, query)
            if path.startswith("/backup/download/"):
                _ok(self, {"message": "Download not available via agent"})
                return
            _error(self, "Not found", 404)
        except Exception as e:
            _error(self, str(e), 500)

    def do_POST(self):
        path = self.path.split("?")[0]
        data = _read_body(self)
        try:
            if path == "/auth/login": return handle_auth_login(self, data)
            if path == "/auth/change-password": return handle_auth_change_password(self, data)
            if path == "/site/create": return handle_create_site(self, data)
            if path == "/site/delete": return handle_delete_site(self, data)
            if path == "/wordpress/install": return handle_install_wordpress(self, data)
            if path == "/wordpress/remove": return handle_remove_wordpress(self, data)
            if path == "/ssl/issue": return handle_issue_ssl(self, data)
            if path == "/ssl/renew": return handle_renew_ssl(self, data)
            if path == "/db/create": return handle_create_database(self, data)
            if path == "/db/delete": return handle_delete_database(self, data)
            if path == "/cron/create": return handle_create_cron(self, data)
            if path == "/cron/delete": return handle_delete_cron(self, data)
            if path == "/cron/toggle": return handle_toggle_cron(self, data)
            if path == "/backup/create": return handle_create_backup(self, data)
            if path == "/backup/restore": return handle_restore_backup(self, data)
            if path == "/backup/delete": return handle_delete_backup(self, data)
            if path == "/php/set-version": return handle_set_php_version(self, data)
            if path == "/settings/update": return handle_update_setting(self, data)
            if path == "/service/restart": return handle_restart_service(self, data)
            if path == "/auth/users": return handle_create_user(self, data)
            if path == "/auth/packages": return handle_create_package(self, data)
            if path == "/email/create": return handle_create_email(self, data)
            if path == "/email/delete": return handle_delete_email(self, data)
            if path == "/ftp/create": return handle_create_ftp(self, data)
            if path == "/ftp/delete": return handle_delete_ftp(self, data)
            if path == "/app/install": return handle_install_app(self, data)
            if path == "/webhook/receive": return handle_webhook_receive(self, data)
            if path.startswith("/file-save/"):
                parts = path[11:].split("/", 1)
                domain = parts[0]
                filepath = "/" + parts[1] if len(parts) > 1 else "/"
                return handle_save_file(self, domain, filepath, data)
            if path.startswith("/file-delete/"):
                parts = path[13:].split("/", 1)
                domain = parts[0]
                filepath = "/" + parts[1] if len(parts) > 1 else "/"
                return handle_delete_file(self, domain, filepath)
            if path.startswith("/file-upload/"):
                parts = path[13:].split("/", 1)
                domain = parts[0]
                filepath = "/" + parts[1] if len(parts) > 1 else "/"
                return handle_upload_file(self, domain, filepath, data)
            if path.startswith("/mkdir/"):
                parts = path[7:].split("/", 1)
                domain = parts[0]
                dirpath = "/" + parts[1] if len(parts) > 1 else "/"
                return handle_mkdir(self, domain, dirpath)
            if path.startswith("/rename/"):
                return handle_rename_file(self, data)
            if path.startswith("/auth/users/"):
                parts = path[11:].split("/")
                if len(parts) >= 1:
                    user_id = parts[0]
                    if path.endswith("/reset"):
                        return handle_reset_password(self, {**data, "id": int(user_id)})
                    return handle_update_user(self, {**data, "id": int(user_id)})
            if path.startswith("/auth/packages/"):
                parts = path[14:].split("/")
                pkg_id = parts[0]
                return handle_update_package(self, {**data, "id": int(pkg_id)})
            if path.startswith("/email/"):
                email_id = path[6:]
                return handle_delete_email(self, {**data, "id": int(email_id)})
            if path.startswith("/ftp/"):
                ftp_id = path[5:]
                return handle_delete_ftp(self, {**data, "id": int(ftp_id)})
            _error(self, "Not found", 404)
        except Exception as e:
            _error(self, str(e), 500)

    def do_PUT(self):
        path = self.path.split("?")[0]
        data = _read_body(self)
        try:
            if path.startswith("/auth/users/"):
                parts = path[11:].split("/")
                user_id = parts[0]
                return handle_update_user(self, {**data, "id": int(user_id)})
            if path.startswith("/auth/packages/"):
                parts = path[14:].split("/")
                pkg_id = parts[0]
                return handle_update_package(self, {**data, "id": int(pkg_id)})
            _error(self, "Not found", 404)
        except Exception as e:
            _error(self, str(e), 500)

    def do_DELETE(self):
        path = self.path.split("?")[0]
        data = _read_body(self) or {}
        try:
            if path.startswith("/auth/users/"):
                parts = path[11:].split("/")
                user_id = parts[0]
                return handle_delete_user(self, {**data, "id": int(user_id)})
            if path.startswith("/auth/packages/"):
                parts = path[14:].split("/")
                pkg_id = parts[0]
                return handle_delete_package(self, {**data, "id": int(pkg_id)})
            _error(self, "Not found", 404)
        except Exception as e:
            _error(self, str(e), 500)


class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    _init_db()
    server = ThreadedHTTPServer(("0.0.0.0", CONF["PORT"]), AgentHandler)
    print(f"ZaydPanel Agent v3.0 running on port {CONF['PORT']}")
    print(f"Database: {CONF['DB_PATH']}")
    sys.stdout.flush()
    signal.signal(signal.SIGTERM, lambda s, f: (server.shutdown(), sys.exit(0)))
    signal.signal(signal.SIGINT, lambda s, f: (server.shutdown(), sys.exit(0)))
    try:
        server.serve_forever()
    except:
        sys.exit(0)


if __name__ == "__main__":
    main()
