#!/bin/bash
# ============================================
# NusaHost - SSL Setup (Staging)
# Domain: staging.pro99.my.id
# ============================================

set -e

DOMAIN="staging.pro99.my.id"
PROJECT_DIR="/opt/nusahost"

echo "=========================================="
echo "  Setup SSL Certificate"
echo "  Domain: $DOMAIN"
echo "=========================================="

if [ "$EUID" -ne 0 ]; then
  echo "Jalankan sebagai root: sudo bash setup-ssl.sh"
  exit 1
fi

cd $PROJECT_DIR

echo "[1/4] Request SSL certificate..."
docker compose run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email admin@pro99.my.id \
  --agree-tos \
  --no-eff-email \
  -d $DOMAIN

echo "[2/4] Update nginx config..."
cp deploy/nginx.conf deploy/nginx.conf.bak
cp deploy/nginx-ssl.conf deploy/nginx.conf

echo "[3/4] Restart nginx..."
docker compose restart nginx

echo "[4/4] Verify..."
sleep 3
echo ""
echo "=========================================="
echo "  SSL berhasil di-install!"
echo "=========================================="
echo ""
echo "  Website: https://$DOMAIN"
echo ""
