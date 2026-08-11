---
Task ID: 1
Agent: Main Agent
Task: Tes daftar pelanggan dari awal - persiapan & perbaikan

Work Log:
- Audit kode app: register, order, payment, callback, dashboard, services, invoices, profile, set-password
- Temukan bug syntax: layout.tsx (`obileMenuOpen` kurang `[`), profile/page.tsx (`essage` kurang `[`)
- Perbaiki bug syntax via SFTP binary replacement
- Setup provision-api systemd service (sebelumnya tidak ada)
- Fix provision-api bind address: 127.0.0.1 -> 0.0.0.0 (supaya container Docker bisa akses)
- Fix provision-api crash loop: tambah SO_REUSEADDR + SO_REUSEPORT
- Update provision_hosting.py: output CREDENTIALS_JSON untuk credential capture
- Update provision-api.py: parse credentials dari stdout dan return di response
- Update payment callback/route.ts: simpan cpUsername/cpPassword/cpDomain ke order DB setelah provisioning
- Rebuild Docker container dengan code fixes
- Bersihkan DB (hapus test users), lalu tes full flow

Stage Summary:
- Bug syntax fixed, provision-api running stable
- Full flow berhasil: Register -> Order -> Callback Payment -> Auto-Provision
- Website berhasil dibuat di CyberPanel (domain: ahmadropi-cmso99.pro99.my.id)
- Credentials tersimpan di DB order (cpUsername, cpPassword, cpDomain)
