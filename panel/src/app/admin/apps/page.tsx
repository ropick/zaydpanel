"use client";
import { useState, useEffect } from "react";
import { api, type SiteInfo, type SiteApps } from "@/lib/api";
import {
  Download, Globe, Loader2, CheckCircle2, XCircle,
  ChevronRight, ArrowLeft, ExternalLink, Search, Trash2,
  Package, RefreshCw, Calendar
} from "lucide-react";
import Link from "next/link";

interface AppInfo {
  id: string; name: string; version: string; icon: string; color: string;
  description: string; category: string; website: string;
  fields: { key: string; label: string; type: string; default: string; required: boolean }[];
}

interface InstallResult {
  success: boolean;
  message: string;
  database?: { database: string; username: string; password: string; host: string };
}

export default function AppInstallerPage() {
  const [apps, setApps] = useState<AppInfo[]>([]);
  const [sites, setSites] = useState<SiteInfo[]>([]);
  const [installed, setInstalled] = useState<SiteApps[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [removing, setRemoving] = useState<string | null>(null);

  // Install state
  const [selectedApp, setSelectedApp] = useState<AppInfo | null>(null);
  const [selectedDomain, setSelectedDomain] = useState("");
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [installing, setInstalling] = useState(false);
  const [installResult, setInstallResult] = useState<InstallResult | null>(null);

  const loadInstalled = () => {
    api.appStatus().then(res => { if (res.success) setInstalled(res.data || []); });
  };

  useEffect(() => {
    Promise.all([api.listApps(), api.listSites(), api.appStatus()]).then(([appsRes, sitesRes, statusRes]) => {
      if (appsRes.success) setApps(appsRes.data || []);
      if (sitesRes.success) setSites(sitesRes.data || []);
      if (statusRes.success) setInstalled(statusRes.data || []);
      setLoading(false);
    });
  }, []);

  const refreshAll = () => {
    setLoading(true);
    Promise.all([api.listSites(), api.appStatus()]).then(([sitesRes, statusRes]) => {
      if (sitesRes.success) setSites(sitesRes.data || []);
      if (statusRes.success) setInstalled(statusRes.data || []);
      setLoading(false);
    });
  };

  const handleRemoveApp = async (domain: string, appId: string, appName: string) => {
    if (!confirm(`Hapus ${appName} dari ${domain}? File aplikasi akan dihapus.`)) return;
    setRemoving(`${domain}/${appId}`);
    const res = await api.removeApp(domain, appId, false);
    setRemoving(null);
    if (res.success) {
      loadInstalled();
    } else {
      alert(res.error || "Gagal menghapus aplikasi");
    }
  };

  const categories = ["All", ...Array.from(new Set(apps.map(a => a.category)))];
  const filtered = apps.filter(a => {
    const matchSearch = a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.description.toLowerCase().includes(search.toLowerCase()) ||
      a.id.toLowerCase().includes(search.toLowerCase());
    const matchCat = category === "All" || a.category === category;
    return matchSearch && matchCat;
  });

  const activeSites = sites.filter(s => s.exists && s.type !== "proxy");

  const startInstall = (app: AppInfo) => {
    setSelectedApp(app);
    setSelectedDomain(activeSites[0]?.domain || "");
    setFieldValues({});
    setInstallResult(null);
  };

  const cancelInstall = () => {
    setSelectedApp(null);
    setSelectedDomain("");
    setFieldValues({});
    setInstallResult(null);
  };

  const handleInstall = async () => {
    if (!selectedApp || !selectedDomain) return;
    setInstalling(true);
    setInstallResult(null);

    // Build fields with domain substitution
    const fields: Record<string, string> = {};
    for (const f of selectedApp.fields) {
      const val = fieldValues[f.key] || f.default.replace("{domain}", selectedDomain);
      if (f.required && !val && f.type === "password" && val === "") {
        // auto-gen password handled by agent
      }
      fields[f.key] = val;
    }

    const res = await api.installApp(selectedDomain, selectedApp.id, fields);
    setInstallResult({
      success: !!res.success,
      message: res.success ? (res.data as any)?.message || "Berhasil!" : (res.error || "Gagal"),
      database: res.success ? (res.data as any)?.database : undefined,
    });
    setInstalling(false);
    if (res.success) loadInstalled();
  };

  if (loading) return <div className="animate-pulse text-surface-500">Loading...</div>;

  // Install modal
  if (selectedApp) return (
    <div className="space-y-6">
      <button onClick={cancelInstall} className="inline-flex items-center gap-2 text-surface-400 hover:text-white text-sm">
        <ArrowLeft size={16} /> Kembali ke Daftar Aplikasi
      </button>

      <div className="card">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-14 h-14 rounded-xl flex items-center justify-center text-white font-bold text-lg flex-shrink-0" style={{ background: selectedApp.color }}>
            {selectedApp.icon}
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">{selectedApp.name} <span className="text-surface-400 font-normal text-sm">v{selectedApp.version}</span></h2>
            <p className="text-surface-400 text-sm">{selectedApp.description}</p>
          </div>
        </div>

        {!installResult ? (
          <div className="space-y-5">
            {/* Domain selector */}
            <div>
              <label className="label">Target Website *</label>
              <select value={selectedDomain} onChange={e => setSelectedDomain(e.target.value)} className="input w-full">
                {activeSites.length === 0 ? (
                  <option value="">Tidak ada website aktif</option>
                ) : activeSites.map(s => (
                  <option key={s.domain} value={s.domain}>{s.domain}</option>
                ))}
              </select>
              {activeSites.length === 0 && (
                <p className="text-yellow-400 text-xs mt-1">Buat website aktif dulu di menu Websites.</p>
              )}
            </div>

            {/* Dynamic fields */}
            {selectedApp.fields.map(f => (
              <div key={f.key}>
                <label className="label">{f.label} {f.required && "*"}</label>
                {f.type === "password" ? (
                  <input
                    type="password"
                    value={fieldValues[f.key] || ""}
                    onChange={e => setFieldValues({ ...fieldValues, [f.key]: e.target.value })}
                    className="input w-full"
                    placeholder={f.default.replace("{domain}", selectedDomain) || "Auto-generate"}
                  />
                ) : (
                  <input
                    type="text"
                    value={fieldValues[f.key] || ""}
                    onChange={e => setFieldValues({ ...fieldValues, [f.key]: e.target.value })}
                    className="input w-full"
                    placeholder={f.default.replace("{domain}", selectedDomain)}
                  />
                )}
                {f.key === "admin_pass" && (
                  <p className="text-surface-500 text-xs mt-1">Kosongkan untuk auto-generate password aman.</p>
                )}
              </div>
            ))}

            {/* Warning */}
            <div className="bg-yellow-900/20 border border-yellow-800/50 rounded-lg p-3 text-sm text-yellow-400">
              ⚠️ Instalasi akan menimpa file yang ada di <code className="text-yellow-300">/home/{selectedDomain || "domain"}/public_html/</code>
            </div>

            <button
              onClick={handleInstall}
              disabled={installing || !selectedDomain}
              className="btn-primary w-full"
            >
              {installing ? (
                <><Loader2 size={16} className="animate-spin" /> Menginstal {selectedApp.name}...</>
              ) : (
                <><Download size={16} /> Instal {selectedApp.name}</>
              )}
            </button>
          </div>
        ) : (
          <div className={`rounded-lg p-5 ${installResult.success ? "bg-brand-900/20 border border-brand-800/50" : "bg-red-900/20 border border-red-800/50"}`}>
            <div className="flex items-center gap-3 mb-3">
              {installResult.success ? <CheckCircle2 size={24} className="text-brand-400" /> : <XCircle size={24} className="text-red-400" />}
              <h3 className="text-lg font-semibold text-white">
                {installResult.success ? "Instalasi Berhasil!" : "Instalasi Gagal"}
              </h3>
            </div>
            <p className="text-surface-300 text-sm mb-4">{installResult.message}</p>

            {installResult.database && (
              <div className="bg-surface-900 rounded-lg p-4 mb-4">
                <h4 className="text-sm font-semibold text-white mb-3">Detail Database</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-surface-400">Database:</span>
                    <code className="text-brand-400">{installResult.database.database}</code>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-surface-400">Username:</span>
                    <code className="text-brand-400">{installResult.database.username}</code>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-surface-400">Password:</span>
                    <code className="text-yellow-400">{installResult.database.password}</code>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-surface-400">Host:</span>
                    <code className="text-brand-400">{installResult.database.host}</code>
                  </div>
                </div>
                <p className="text-yellow-500 text-xs mt-3">⚠️ Simpan password ini! Tidak bisa dilihat lagi.</p>
              </div>
            )}

            <div className="flex gap-3">
              {selectedDomain && (
                <a href={`https://${selectedDomain}`} target="_blank" rel="noopener noreferrer" className="btn-primary text-xs">
                  <ExternalLink size={14} /> Buka Website
                </a>
              )}
              <button onClick={cancelInstall} className="btn-secondary text-xs">Tutup</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // App catalog grid
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">App Installer</h1>
          <p className="text-surface-400 text-sm mt-1">Install aplikasi ke website Anda dengan 1 klik — seperti Softaculous</p>
        </div>
        <Link href="/admin/sites" className="btn-secondary text-xs">
          <Globe size={14} /> Kelola Website
        </Link>
      </div>

      {/* Installed Apps status */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Package size={16} className="text-brand-400" /> Status Instalasi Aplikasi
            <span className="text-xs text-surface-500 font-normal">
              ({installed.reduce((n, s) => n + s.apps.length, 0)} terpasang)
            </span>
          </h2>
          <button onClick={refreshAll} className="btn-ghost text-xs" disabled={loading}>
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>
        {installed.filter(s => s.apps.length > 0).length === 0 ? (
          <p className="text-surface-500 text-sm py-2">Belum ada aplikasi yang terinstall.</p>
        ) : (
          <div className="space-y-3">
            {installed.filter(s => s.apps.length > 0).map(site => (
              <div key={site.domain} className="bg-surface-800/60 rounded-lg p-3">
                <p className="text-sm font-medium text-white flex items-center gap-2 mb-2">
                  <Globe size={14} className="text-surface-400" /> {site.domain}
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {site.apps.map(app => (
                    <div key={app.app_id} className="flex items-center gap-2 bg-surface-900 rounded-lg px-3 py-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white font-medium truncate">{app.app_name} {app.version && <span className="text-xs text-surface-500">v{app.version}</span>}</p>
                        <p className="text-xs text-surface-400 flex items-center gap-1">
                          <Calendar size={10} />
                          {app.installed_at ? app.installed_at.replace("T", " ").slice(0, 16) : "—"}
                          {app.needs_web_setup && <span className="text-yellow-400 ml-1">(butuh setup web)</span>}
                        </p>
                      </div>
                      {app.admin_url && (
                        <a href={app.admin_url} target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:text-brand-300" title={app.admin_url}>
                          <ExternalLink size={14} />
                        </a>
                      )}
                      <button
                        onClick={() => handleRemoveApp(site.domain, app.app_id, app.app_name)}
                        disabled={removing === `${site.domain}/${app.app_id}`}
                        className="text-red-400 hover:text-red-300 disabled:opacity-50"
                        title={`Hapus ${app.app_name}`}
                      >
                        {removing === `${site.domain}/${app.app_id}` ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Search & Filter */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex items-center gap-2 flex-1">
            <Search size={16} className="text-surface-400" />
            <input type="text" value={search} onChange={e => setSearch(e.target.value)} className="input flex-1" placeholder="Cari aplikasi..." />
          </div>
          <div className="flex gap-2 flex-wrap">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${category === cat ? "bg-brand-600 text-white" : "bg-surface-800 text-surface-400 hover:text-white hover:bg-surface-700"}`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="card text-center">
          <p className="text-2xl font-bold text-white">{apps.length}</p>
          <p className="text-surface-400 text-xs">Aplikasi</p>
        </div>
        <div className="card text-center">
          <p className="text-2xl font-bold text-brand-400">{activeSites.length}</p>
          <p className="text-surface-400 text-xs">Website Aktif</p>
        </div>
        <div className="card text-center">
          <p className="text-2xl font-bold text-blue-400">{sites.filter(s => s.has_wp).length}</p>
          <p className="text-surface-400 text-xs">WordPress</p>
        </div>
        <div className="card text-center">
          <p className="text-2xl font-bold text-green-400">{sites.filter(s => s.ssl).length}</p>
          <p className="text-surface-400 text-xs">SSL Active</p>
        </div>
      </div>

      {/* Apps Grid */}
      {filtered.length === 0 ? (
        <div className="card text-center py-12">
          <Download size={48} className="mx-auto text-surface-700 mb-4" />
          <p className="text-surface-400">Tidak ada aplikasi ditemukan.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(app => (
            <div key={app.id} className="card hover:border-brand-600/50 transition-colors group cursor-pointer" onClick={() => startInstall(app)}>
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-xl flex items-center justify-center text-white font-bold text-lg flex-shrink-0 shadow-lg" style={{ background: app.color }}>
                  {app.icon}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-white font-semibold">{app.name}</h3>
                    <span className="text-xs text-surface-500">v{app.version}</span>
                  </div>
                  <p className="text-surface-400 text-sm mt-1 line-clamp-2">{app.description}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-surface-800 text-surface-400">{app.category}</span>
                    <span className="text-xs text-brand-400 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                      Install <ChevronRight size={12} />
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info */}
      <div className="card text-center text-surface-500 text-sm">
        <p>App Installer mirip Softaculous — install aplikasi web populer ke website Anda dengan 1 klik.</p>
        <p className="mt-1 text-xs">WordPress, Joomla, Laravel, Nextcloud, PrestaShop, phpMyAdmin</p>
      </div>
    </div>
  );
}
