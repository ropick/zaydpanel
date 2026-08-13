# ZaydPanel

<div align="center">

**Free, Open-Source Multi-User Control Panel for Shared Hosting**

ZaydPanel adalah control panel gratis dan open-source untuk mengelola shared hosting. Dirancang sederhana seperti CloudPanel, tapi dengan dukungan multi-user — cocok untuk bisnis sewa hosting kecil-menengah.

[![GitHub release](https://img.shields.io/badge/version-2.2-green)](https://github.com/ropick/zaydpanel)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Made with Python](https://img.shields.io/badge/Agent-Python3-yellow)](agent/)
[![Made with Next.js](https://img.shields.io/badge/Panel-Next.js-black)](panel/)

<a href="https://sociabuzz.com/rofiqrpk"><img src="https://img.shields.io/badge/Support-Donasi-orange" alt="Donate" /></a>

</div>

---

## ✨ Fitur

- **Multi-User** — Admin + Customer panel terpisah
- **Website Management** — Buat/hapus website, PHP-FPM pool per site, Nginx vhost otomatis
- **WordPress 1-Click Install** — Install WordPress langsung dari panel
- **MySQL Manager** — Buat/hapus database per website
- **SSL Otomatis** — Let's Encrypt SSL dengan satu klik
- **File Manager** — Kelola file website langsung dari browser (view, edit, delete)
- **Server Monitoring** — Info CPU, RAM, Disk, Network I/O, Load Average real-time
- **Process & Cron Management** — Monitor top processes dan kelola cron jobs
- **PHP Manager** — Kelola versi PHP per website
- **Log Viewer** — Lihat access & error log per website
- **Backup System** — Backup dan restore website
- **Dark Theme UI** — Interface modern dan responsif
- **Standalone** — Bisa diinstall di VPS mana saja (AlmaLinux, Ubuntu, Debian)
- **Gratis Selamanya** — 100% open-source, tanpa lisensi bayar

## 🏗️ Arsitektur

```
zaydpanel/
├── agent/                  # Python daemon (HTTP API di port 8442)
│   └── zaydpanel-agent.py
├── panel/                  # Next.js web panel (Admin UI)
│   ├── src/
│   │   ├── app/            # Pages (login, dashboard, sites, databases, server, files)
│   │   │   ├── admin/      # Admin pages (13 routes)
│   │   │   │   ├── page.tsx           # Dashboard
│   │   │   │   ├── sites/             # Website management + create
│   │   │   │   ├── databases/         # MySQL management
│   │   │   │   ├── server/            # Server info
│   │   │   │   ├── processes/         # Process monitoring
│   │   │   │   ├── ssl/               # SSL certificates
│   │   │   │   ├── php/               # PHP version manager
│   │   │   │   ├── cron/              # Cron jobs
│   │   │   │   ├── logs/              # Log viewer
│   │   │   │   ├── backups/           # Backup system
│   │   │   │   └── settings/          # System settings
│   │   │   └── login/       # Login page
│   │   ├── components/     # Sidebar navigation
│   │   └── lib/            # API client, auth, utilities
│   └── package.json
├── scripts/                # Deploy scripts
├── docs/                   # Logo dan dokumentasi
├── README.md
└── LICENSE
```

### Komponen

| Komponen | Teknologi | Deskripsi |
|----------|-----------|-----------|
| **ZaydPanel Agent** | Python 3 | Daemon HTTP yang menjalankan command server (create site, PHP-FPM, Nginx, MySQL, WP-CLI, SSL) |
| **ZaydPanel Panel** | Next.js 15 + Tailwind CSS | Web UI admin dengan dark theme, responsif, real-time monitoring |
| **API Proxy** | Next.js API Routes | Server-side proxy ke agent, inject Bearer token secara aman |

## 🚀 Quick Start

```bash
git clone https://github.com/ropick/zaydpanel.git
cd zaydpanel

# Jalankan agent
sudo python3 agent/zaydpanel-agent.py

# Jalankan panel
cd panel
npm install
npm run dev
# Buka http://localhost:2080
```

## 📋 Requirement Server

- OS: AlmaLinux 9+, Ubuntu 22.04+, Debian 12+
- RAM: Minimal 1GB (recommend 2GB+)
- Disk: Minimal 10GB
- Software: Nginx, MariaDB, PHP-FPM, WP-CLI, acme.sh
- Akses: Root atau sudo

## 🔌 Agent API

Agent berjalan di `http://127.0.0.1:8442` dengan Bearer token auth.

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/health` | Health check |
| GET | `/sites` | List semua website |
| GET | `/server-info` | Info CPU, RAM, Disk, Network, Load |
| GET | `/processes` | Top processes |
| GET | `/files/{domain}/{path}` | List files |
| GET | `/file-content/{domain}/{path}` | Baca file |
| GET | `/ssl/list` | List SSL certificates |
| GET | `/db/list` | List databases |
| GET | `/php/versions` | PHP versions |
| GET | `/cron/list` | List cron jobs |
| GET | `/logs/{domain}/{type}` | View logs |
| GET | `/backup/list` | List backups |
| POST | `/site/create` | Buat website baru (Nginx + PHP-FPM + MySQL + User) |
| POST | `/site/delete` | Hapus website |
| POST | `/wordpress/install` | Install WordPress 1-click |
| POST | `/ssl/issue` | Issue SSL Let's Encrypt |
| POST | `/db/create` | Buat database MySQL |
| POST | `/db/delete` | Hapus database |
| POST | `/file-save/{domain}/{path}` | Simpan/edit file |
| POST | `/file-upload/{domain}/{path}` | Upload file (base64) |
| POST | `/file-delete/{domain}/{path}` | Hapus file |
| POST | `/mkdir/{domain}` | Buat directory |
| POST | `/rename/{domain}` | Rename file/directory |

## 🖥️ Panel Pages

- **Dashboard** — Overview server (CPU, RAM, Disk, Network, Load, Top Processes, Websites) auto-refresh 15s
- **Websites** — List semua website dengan badge (Active, Proxy, WordPress, SSL), aksi cepat (WordPress, SSL, Files, Hapus)
- **Create Website** — Form buat website baru
- **Databases** — Management database MySQL per website
- **Server Info** — Monitoring resource server real-time (Network I/O, Load Average, Uptime)
- **Processes** — Monitor top processes (CPU, RAM)
- **SSL Certificates** — Issue dan renew SSL Let's Encrypt
- **PHP Manager** — Kelola versi PHP per website
- **Cron Jobs** — Kelola scheduled tasks
- **Log Viewer** — Lihat access & error log per website
- **Backups** — Backup dan restore website
- **Settings** — System settings

## 🗺️ Roadmap

- [x] Fase 1: Agent daemon + API Proxy
- [x] Fase 1: Admin panel (Dashboard, Sites, Databases, Server Info, File Manager)
- [x] Fase 1: WordPress 1-click install
- [x] Fase 1: SSL management
- [x] Fase 1: File Manager (view, edit, delete, upload, mkdir, rename)
- [x] Fase 1: Process monitoring & Cron management
- [x] Fase 1: PHP version management
- [x] Fase 1: Log viewer & Backup system
- [ ] Fase 2: Customer panel terpisah
- [ ] Fase 2: Multi-admin & role management
- [ ] Fase 3: Email hosting
- [ ] Fase 3: FTP accounts
- [ ] Fase 3: Billing integration hook

## 💖 Support & Donasi

ZaydPanel gratis dan akan selalu gratis. Jika project ini bermanfaat untuk Anda, dukung pengembangan dengan donasi:

**👉 [https://sociabuzz.com/rofiqrpk](https://sociabuzz.com/rofiqrpk)**

Terima kasih atas dukungannya!

## 📄 License

MIT License — Gratis untuk penggunaan pribadi dan komersial.
