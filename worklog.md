# aaPanel Fresh Installation - Work Log
## Date: 2026-08-07
## Server: 168.110.210.148 (Oracle ARM, AlmaLinux 9)

### What was done:
1. Completely removed old aaPanel installation
2. Downloaded panel_7_en.zip (56MB) from node.aapanel.com
3. Created Python 3.12 venv at /www/server/panel/pyenv
4. Installed required packages: flask==2.2.5, gevent, psutil, pymongo, pyopenssl, bcrypt, pyinotify, etc.
5. Fixed Python 3.9/3.10 compatibility issues in source code:
   - Type annotations (dict | List -> Union[dict, List])
   - @clean_cahce() staticmethod decorator in theme_config.py
   - ThemeConfigManager.return_message static method calls
6. Created SQLite databases (default.db with user, system.db with sites/databases tables)
7. Set panel to HTTP mode (no SSL) on port 36977
8. Set debug mode (local static files)
9. Updated Docker nginx to proxy panel.pro99.my.id -> 172.17.0.1:36977 (HTTP)

### Credentials:
- URL: http://panel.pro99.my.id/login
- Username: ib0xgxtd
- Password: Pro99@2026
- Admin path: /panel (set but not used in current config)
- Port: 36977 (HTTP)

### Notes:
- panelSetup.init() returns None which causes HEAD requests to return 500 (Flask issue)
- GET requests work fine - login page returns HTTP 200 with 181KB HTML
- BT-Task is NOT running (to save CPU on 1 OCPU VPS)
- SSL is disabled (ssl.pl removed) - panel runs on HTTP only
- Cloudflare proxies external traffic

### Files modified on VPS:
- /www/server/panel/class/public/common.py (type annotations)
- /www/server/panel/class_v2/theme_config.py (decorator fix, return_message fix)
- /opt/nusahost/deploy/nginx.conf (panel.pro99.my.id server block)
- /www/server/panel/data/port.pl (36977)
- /www/server/panel/data/admin_path.pl (/panel)
- /www/server/panel/default.pl (Pro99@2026)
- /www/server/panel/data/default.db (user credentials)
- /www/server/panel/data/debug.pl (exists = debug mode)
