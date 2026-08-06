# ============================================
# DEPLOY NusaHost ke VPS Oracle ARM
# IP: 168.110.210.148 | Domain: pro99.my.id
# ============================================

## LANGKAH 0: Persiapan DNS (Lakukan DULU)

Login ke panel domain Anda (tempat beli pro99.my.id), tambahkan DNS Record:

| Type  | Name   | Value              | TTL  |
|-------|--------|---------------------|------|
| A     | @      | 168.110.210.148    | Auto |
| A     | www    | 168.110.210.148    | Auto |

Tunggu DNS propagate (bisa 5-30 menit).

Cek: `nslookup pro99.my.id` atau `ping pro99.my.id`


## LANGKAH 1: Upload File ke VPS

Dari komputer lokal Anda, jalankan:

```bash
# Ganti dengan path project yang benar
# Pastikan Anda sudah build di environment development (sudah done)
# Upload folder project ke VPS

# Opsi A: rsync (rekomendasi)
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude 'db' \
  ./ root@168.110.210.148:/opt/nusahost/

# Opsi B: scp (alternatif)
# Pertama zip dulu file yang dibutuhkan
cd /home/z/my-project
tar czf nusahost-deploy.tar.gz \
  src/ public/ prisma/ package.json bun.lock \
  next.config.ts tailwind.config.ts postcss.config.mjs \
  tsconfig.json components.json eslint.config.mjs \
  deploy/

scp nusahost-deploy.tar.gz root@168.110.210.148:/opt/
```

Di VPS:
```bash
cd /opt
mkdir -p nusahost
cd nusahost
tar xzf /opt/nusahost-deploy.tar.gz
```


## LANGKAH 2: Login ke VPS & Jalankan Deploy

```bash
# SSH ke VPS
ssh opc@168.110.210.148
# (atau root jika sudah diset)

# Jalankan deployment script
cd /opt/nusahost
sudo bash deploy/deploy.sh
```

Script akan otomatis:
- Update system
- Install Docker & Docker Compose
- Buka port firewall (80, 443)
- Build Docker image (ARM64)
- Start containers (app + nginx)


## LANGKAH 3: Setup SSL Certificate

Setelah container berjalan dan DNS sudah resolve:

```bash
cd /opt/nusahost
sudo bash deploy/setup-ssl.sh
```


## LANGKAH 4: Verify

```bash
# Cek container status
cd /opt/nusahost
docker compose ps

# Cek logs
docker compose logs -f app

# Test website
curl -I https://pro99.my.id
```


## COMMAND BERMANFAAT

```bash
# Lihat logs real-time
cd /opt/nusahost && docker compose logs -f

# Restart semua
cd /opt/nusahost && docker compose restart

# Stop semua
cd /opt/nusahost && docker compose down

# Rebuild setelah update code
cd /opt/nusahost && docker compose build --no-cache && docker compose up -d

# Hanya restart app
cd /opt/nusahost && docker compose restart app

# Backup database
docker cp nusahost-app:/app/db/custom.db ./backup-$(date +%Y%m%d).db
```


## UPDATE CODE KEDEPAN

```bash
# Dari lokal
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude 'db' \
  ./ root@168.110.210.148:/opt/nusahost/

# Di VPS
cd /opt/nusahost
docker compose build --no-cache
docker compose up -d
```


## TROUBLESHOOTING

1. **Port 80/443 tidak bisa diakses**
   - Oracle ARM perlu buka port di iptables (sudah di script)
   - Juga cek Security List di Oracle Cloud Console > Networking

2. **Docker build gagal ARM64**
   - Pastikan menggunakan node:20-alpine (multi-arch)
   - `docker buildx ls` untuk cek platform support

3. **DNS belum resolve**
   - `nslookup pro99.my.id` untuk cek
   - Tunggu hingga 48 jam untuk full propagation

4. **SSL certbot gagal**
   - Pastikan DNS sudah resolve ke IP VPS
   - Cek port 80 terbuka: `curl -I http://pro99.my.id`
