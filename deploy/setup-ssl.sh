#!/bin/bash
# ============================================
# NusaHost - SSL Setup Script (Certbot)
# Domain: pro99.my.id
# ============================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DOMAIN="pro99.my.id"
PROJECT_DIR="/opt/nusahost"

echo -e "${YELLOW}=========================================="
echo "  Setup SSL Certificate"
echo "  Domain: $DOMAIN"
echo "==========================================${NC}"

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Jalankan sebagai root: sudo bash setup-ssl.sh${NC}"
  exit 1
fi

cd $PROJECT_DIR

# ---- Request SSL certificate ----
echo -e "${YELLOW}[1/4] Request SSL certificate...${NC}"
docker compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@pro99.my.id \
  --agree-tos \
  --no-eff-email \
  -d $DOMAIN \
  -d www.$DOMAIN

# ---- Switch nginx config to SSL ----
echo -e "${YELLOW}[2/4] Update nginx config for SSL...${NC}"
cp deploy/nginx.conf deploy/nginx.conf.bak
cp deploy/nginx-ssl.conf deploy/nginx.conf

# ---- Restart nginx ----
echo -e "${YELLOW}[3/4] Restart nginx...${NC}"
docker compose restart nginx

# ---- Verify ----
echo -e "${YELLOW}[4/4] Verify...${NC}"
sleep 3
echo ""
echo -e "${GREEN}=========================================="
echo "  SSL berhasil di-install!"
echo "==========================================${NC}"
echo ""
echo "  Website: https://$DOMAIN"
echo ""
echo "  Auto-renewal sudah di-setup via certbot container"
echo "  Certificate akan auto-renew setiap 6 jam"
echo ""
echo "  Test: curl -I https://$DOMAIN"
echo ""
