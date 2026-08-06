#!/bin/bash
# ============================================
# Quick Upload Script - Upload NusaHost to VPS
# Run dari environment development
# ============================================

set -e

VPS_IP="168.110.210.148"
VPS_USER="opc"
PROJECT_DIR="/home/z/my-project"
REMOTE_DIR="/opt/nusahost"

echo "=========================================="
echo "  Upload NusaHost ke VPS"
echo "  IP: $VPS_IP"
echo "=========================================="
echo ""

# Create tarball
echo "[1/3] Membuat archive..."
cd $PROJECT_DIR
tar czf /tmp/nusahost.tar.gz \
  src/ public/ prisma/ package.json bun.lock \
  next.config.ts tailwind.config.ts postcss.config.mjs \
  tsconfig.json components.json eslint.config.mjs \
  deploy/ .env

echo "[2/3] Upload ke VPS..."
ssh $VPS_USER@$VPS_IP "mkdir -p $REMOTE_DIR"
scp /tmp/nusahost.tar.gz $VPS_USER@$VPS_IP:/tmp/

echo "[3/3] Extract di VPS..."
ssh $VPS_USER@$VPS_IP "cd $REMOTE_DIR && tar xzf /tmp/nusahost.tar.gz && rm /tmp/nusahost.tar.gz"

echo ""
echo "Upload selesai!"
echo ""
echo "Selanjutnya, login ke VPS:"
echo "  ssh $VPS_USER@$VPS_IP"
echo "  cd $REMOTE_DIR"
echo "  sudo bash deploy/deploy.sh"
echo ""

rm -f /tmp/nusahost.tar.gz
