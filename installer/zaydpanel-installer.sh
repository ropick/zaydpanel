#!/bin/bash
# ZaydPanel Installer - 1-command setup for AlmaLinux 9/Ubuntu 22.04+/Debian 12+
# Usage: curl -sSL https://raw.githubusercontent.com/ropick/zaydpanel/main/installer/zaydpanel-installer.sh | sudo bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Detect OS
if [ -f /etc/alma-release ] || [ -f /etc/rocky-release ] || [ -f /etc/oracle-release ]; then
    PKG="dnf"
elif [ -f /etc/ubuntu-release ] || [ -f /etc/debian_version ]; then
    PKG="apt-get"
else err "Unsupported OS"; fi

check_root() { [ "$(id -u)" -ne 0 ] && err "Run as root: sudo $0"; }

install_packages() {
    info "Installing packages..."
    if [ "$PKG" = "dnf" ]; then
        dnf install -y nginx mariadb-server python3 python3-pip php php-fpm php-mysqlnd php-json php-mbstring php-xml php-gd php-curl php-zip php-opcache php-intl wget curl tar git unzip which bc jq sqlite >/dev/null 2>&1
        dnf install -y epel-release certbot python3-certbot-nginx >/dev/null 2>&1 || true
    else
        apt-get update -qq
        apt-get install -y nginx mariadb-server python3 python3-pip php-fpm php-mysql php-json php-mbstring php-xml php-gd php-curl php-zip php-opcache php-intl wget curl tar git unzip which bc jq sqlite3 >/dev/null 2>&1
        apt-get install -y certbot python3-certbot-nginx >/dev/null 2>&1 || true
    fi
    ok "Packages installed"
}

setup_mariadb() {
    info "Setting up MariaDB..."
    systemctl enable --now mariadb >/dev/null 2>&1
    mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY ''; FLUSH PRIVILEGES;" 2>/dev/null || true
    mysql -e "DELETE FROM mysql.user WHERE User=''; DROP DATABASE IF EXISTS test; FLUSH PRIVILEGES;" 2>/dev/null || true
    ok "MariaDB configured"
}

setup_php_fpm() {
    info "Configuring PHP-FPM..."
    if [ "$PKG" = "dnf" ]; then
        systemctl enable php-fpm >/dev/null 2>&1 && systemctl start php-fpm >/dev/null 2>&1
    else
        VER=$(php -r "echo PHP_MAJOR_VERSION.'.'.PHP_MINOR_VERSION;")
        systemctl enable "php${VER}-fpm" >/dev/null 2>&1 && systemctl start "php${VER}-fpm" >/dev/null 2>&1
    fi
    ok "PHP-FPM configured"
}

setup_nginx() {
    info "Configuring Nginx..."
    [ -f /etc/nginx/conf.d/default.conf ] && mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/00-default.conf.bak
    cat > /etc/nginx/nginx.conf << 'NGINX'
worker_processes auto;
events { worker_connections 1024; }
http {
    include mime.types; default_type application/octet-stream;
    sendfile on; tcp_nopush on; tcp_nodelay on; keepalive_timeout 65; gzip on;
    include /etc/nginx/conf.d/*.conf;
}
NGINX
    mkdir -p /etc/nginx/conf.d
    systemctl enable nginx >/dev/null 2>&1 && (systemctl reload nginx 2>/dev/null || systemctl start nginx)
    ok "Nginx configured"
}

install_wpcli() {
    info "Installing WP-CLI..."
    curl -sS https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar -o /usr/local/bin/wp 2>/dev/null
    chmod +x /usr/local/bin/wp 2>/dev/null
    ok "WP-CLI installed"
}

install_acme() {
    curl -sS https://get.acme.sh | sh -s email=admin@example.com >/dev/null 2>&1 || true
    ok "SSL tools installed"
}

install_agent() {
    info "Installing ZaydPanel Agent v3.0..."
    mkdir -p /opt/zaydpanel/{agent,backups,cron,data,stats}
    pip3 install paramiko 2>/dev/null || true
    AGENT_URL="https://raw.githubusercontent.com/ropick/zaydpanel/main/agent/zaydpanel-agent.py"
    curl -sSL "$AGENT_URL" -o /opt/zaydpanel/agent/zaydpanel-agent.py 2>/dev/null
    chmod +x /opt/zaydpanel/agent/zaydpanel-agent.py
    cat > /etc/systemd/system/zaydpanel-agent.service << EOF
[Unit]
Description=ZaydPanel Agent
After=network.target mariadb.service nginx.service
[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /opt/zaydpanel/agent/zaydpanel-agent.py
Restart=always
RestartSec=5
Environment=ZAYDPANEL_AGENT_PORT=8442
Environment=ZAYDPANEL_AGENT_SECRET=zc-agent-2026-secret
[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable zaydpanel-agent >/dev/null 2>&1
    systemctl start zaydpanel-agent
    ok "Agent installed and running"
}

setup_firewall() {
    info "Configuring firewall..."
    if command -v firewall-cmd &>/dev/null; then
        firewall-cmd --permanent --add-service=http --add-service=https >/dev/null 2>&1 && firewall-cmd --reload >/dev/null 2>&1
    elif command -v ufw &>/dev/null; then
        ufw allow 80/tcp 443/tcp >/dev/null 2>&1
    fi
    ok "Firewall configured"
}

verify() {
    echo ""
    echo "======================================"
    echo -e "${GREEN} ZaydPanel Installed Successfully!${NC}"
    echo "======================================"
    echo ""
    for svc in nginx mariadb zaydpanel-agent; do
        systemctl is-active --quiet "$svc" 2>/dev/null && ok "$svc running" || warn "$svc not running"
    done
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Deploy panel: copy .next/standalone to /opt/zaydpanel/panel/"
    echo "2. Setup panel systemd service"
    echo "3. SSL: certbot --nginx -d panel.yourdomain.com"
    echo "4. Login: admin / zaydpanel2026"
    echo ""
}

echo ""
echo "  ZaydPanel Installer v3.0"
echo "  Free Multi-User Hosting Control Panel"
echo ""
check_root
install_packages
setup_mariadb
setup_php_fpm
setup_nginx
install_wpcli
install_acme
install_agent
mkdir -p /opt/zaydpanel/panel
setup_firewall
verify
