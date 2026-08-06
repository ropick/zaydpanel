# ============================================
# NusaHost - VPS Deployment Script
# Oracle ARM | Ubuntu 22.04+ | ARM64
# Domain: pro99.my.id | IP: 168.110.210.148
# ============================================

set -e
echo "=========================================="
echo "  NusaHost - VPS Deployment"
echo "  Oracle ARM | pro99.my.id"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ---- Check if running as root ----
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Jalankan script ini sebagai root: sudo bash deploy.sh${NC}"
  exit 1
fi

# ---- Update system ----
echo -e "${YELLOW}[1/7] Update system...${NC}"
apt-get update -y
apt-get upgrade -y

# ---- Install Docker ----
echo -e "${YELLOW}[2/7] Install Docker...${NC}"
if ! command -v docker &> /dev/null; then
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
    echo "Docker sudah terinstall."
fi

# ---- Install Docker Compose (standalone) ----
echo -e "${YELLOW}[3/7] Install Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi
docker --version
docker compose version
docker-compose --version 2>/dev/null || true

# ---- Firewall (Oracle ARM iptables) ----
echo -e "${YELLOW}[4/7] Configure firewall...${NC}"
# Oracle ARM uses iptables by default
# Open ports 80, 443, 22, 3000
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 3000 -j ACCEPT

# Save iptables rules
apt-get install -y iptables-persistent
netfilter-persistent save

echo "Ports opened: 80 (HTTP), 443 (HTTPS), 3000 (App)"

# ---- Create project directory ----
echo -e "${YELLOW}[5/7] Setup project...${NC}"
PROJECT_DIR="/opt/nusahost"
mkdir -p $PROJECT_DIR
mkdir -p $PROJECT_DIR/deploy

# Copy files (assume files are in same directory as script)
# If using rsync from local machine, files should already be here
echo "Copy project files ke $PROJECT_DIR..."

# Check if source files exist (for direct copy on VPS)
if [ -f "Dockerfile" ]; then
    cp -r ./* $PROJECT_DIR/ 2>/dev/null || true
else
    echo "File project belum ada. Pastikan file sudah di-upload ke $PROJECT_DIR"
fi

cd $PROJECT_DIR

# ---- Build & Start containers ----
echo -e "${YELLOW}[6/7] Build & Start containers...${NC}"
docker compose build --no-cache
docker compose up -d

echo ""
echo -e "${YELLOW}[7/7] Status...${NC}"
docker compose ps

echo ""
echo -e "${GREEN}=========================================="
echo "  Deploy berhasil!"
echo "==========================================${NC}"
echo ""
echo "  URL: http://168.110.210.148"
echo "  (Setelah DNS propagate: https://pro99.my.id)"
echo ""
echo "  Command penting:"
echo "  - Logs:        cd $PROJECT_DIR && docker compose logs -f"
echo "  - Restart:     cd $PROJECT_DIR && docker compose restart"
echo "  - Stop:        cd $PROJECT_DIR && docker compose down"
echo "  - Rebuild:     cd $PROJECT_DIR && docker compose build --no-cache && docker compose up -d"
echo ""
echo "  NEXT STEP: Setup SSL Certificate"
echo "  Jalankan:  sudo bash /opt/nusahost/deploy/setup-ssl.sh"
echo ""
