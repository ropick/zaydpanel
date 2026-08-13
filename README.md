# ZaydPanel - Shared Hosting Control Panel

Enterprise-grade shared hosting control panel built with Next.js 15 and Python.

## Architecture

- **Panel**: Next.js 15 + Tailwind CSS (port 2080)
- **Agent**: Python HTTP server (port 8442, internal only)
- **Server**: Oracle ARM VPS, AlmaLinux 9

## Features

- Dashboard with real-time server stats
- Website management (create, delete, list)
- WordPress installation
- SSL certificate management (Let's Encrypt)
- Database management (MariaDB)
- File manager
- Process monitoring
- PHP version management
- Cron job management
- Backup management
- Log viewer

## Deploy

```bash
# Build panel
cd panel && npm run build

# Deploy agent
sudo cp agent/zaydpanel-agent.py /opt/zaydpanel/agent/
sudo systemctl restart zaydpanel-agent

# Deploy panel
# Copy .next/standalone + .next/static to /opt/zaydpanel/panel/
sudo systemctl restart zaydpanel-panel
```
