"use client";
import { useState, useEffect } from "react";
import { api, type SiteInfo } from "@/lib/api";
import {
  Zap, Download, Globe, CheckCircle, XCircle, Loader2, ArrowRight,
  Database, Shield, ChevronDown, ChevronUp, ExternalLink, Trash2,
  ShoppingBag, Rocket, Lock, FileSpreadsheet, Cloud, Code,
} from "lucide-react";
import Link from "next/link";

interface AppInfo {
  id: string;
  name: string;
  version: string;
  icon: string;
  color: string;
  description: string;
  category: string;
  website: string;
  fields: { key: string; label: string; type: string; default: string; required: boolean }[];
}

interface InstallResult {
  success: boolean;
  message: string;
  admin_url?: string;
  admin_user?: string;
  admin_pass?: string;
  database?: { database: string; username: string; password: string; host: string };
  needs_web_setup?: boolean;
}

export default function CustomerAppsPage() {
  const [apps, setApps] = useState<AppInfo[]>([]);
  const [sites, setSites] = useState<SiteInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApp, setSelectedApp] = useState<AppInfo | null>(null);
  const [selectedSite, setSelectedSite] = useState<string>("");
  const [installing, setInstalling] = useState(false);
  const [result, setResult] = useState<InstallResult | null>(null);
  const [expandedApp, setExpandedApp] = useState<string | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});

  useEffect(() => {
    Promise.all([
      api.listApps(),
      api.listSites(),
    ]).then(([appsRes, sitesRes]) => {
      if (appsRes.success) setApps(appsRes.data || []);
      if (sitesRes.success) setSites((sitesRes.data || []).filter(s => s.exists));
      setLoading(false);
    });
  }, []);

  const activeSites = sites.filter(s => s.exists && !s.has_wp);
  const wpSites = sites.filter(s => s.has_wp);

  const handleSelectApp = (app: AppInfo) => {
    setSelectedApp(prev => prev?.id === app.id ? null : app);
    setExpandedApp(prev => prev === app.id ? null : app.id);
    setFormData({});
    setResult(null);
    const defaults: Record<string, string> = {};
    app.fields.forEach(f => {
      defaults[f.key] = f.default.replace("{domain}", selectedSite || "mysite.com");
    });
    setFormData(defaults);
  };

  const handleInstall = async () => {
    if (!selectedApp || !selectedSite) return;
    setInstalling(true);
    const body: Record<string, string> = {
      domain: selectedSite,
      app_type: selectedApp.id,
      ...formData,
    };
    const res = await api.installApp(selectedSite, selectedApp.id, formData);
    setInstalling(false);
    if (res.success && res.data) {
      const d = res.data as any;
      setResult({
        success: true,
        message: d.message || `${selectedApp.name} installed!`,
        admin_url: d.admin_url,
        admin_user: d.admin_user,
        admin_pass: d.admin_pass,
        database: d.database,
        needs_web_setup: d.needs_web_setup,
      });
      const sitesRes = await api.listSites();
      if (sitesRes.success) setSites(sitesRes.data || []);
    } else {
      setResult({
        success: false,
        message: (res as any).error || "Installation failed",
      });
    }
  };

  const handleRemoveWP = async (domain: string) => {
    if (!confirm(`Hapus WordPress dari ${domain}? Semua file dan data akan dihapus.`)) return;
    const token = typeof window !== "undefined" ? (() => { try { const d = JSON.parse(localStorage.getItem("zaydpanel_auth") || "{}"); return d.token || ""; } catch { return ""; }})() : "";
    const res = await fetch("/api/agent/wordpress/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ domain, drop_database: true }),
    });
    const data = await res.json();
    if (data.success) {
      setResult({ success: true, message: data.data?.message || "WordPress removed!" });
      const sitesRes = await api.listSites();
      if (sitesRes.success) setSites(sitesRes.data || []);
    } else {
      setResult({ success: false, message: data.error || "Failed to remove" });
    }
  };

  const getAppIcon = (app: AppInfo) => {
    const iconMap: Record<string, any> = {
      wordpress: Code,
      joomla: ShoppingBag,
      laravel: Rocket,
      nextcloud: Cloud,
      prestashop: ShoppingBag,
      phpmyadmin: Database,
    };
    const Icon = iconMap[app.id] || Zap;
    return <Icon size={28} />;
  };

  const getCategoryLabel = (cat: string) => {
    const labels: Record<string, string> = {
      CMS: "CMS / Blog",
      Framework: "Framework",
      Ecommerce: "E-Commerce",
      Tools: "Database & Tools",
    };
    return labels[cat] || cat;
  };

  const categories = [...new Set(apps.map(a => a.category))];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">App Installer</h1>
          <p className="text-surface-400 text-sm mt-1">Install aplikasi populer dengan satu klik — seperti Softaculous</p>
        </div>
        <Link href="/customer/sites" className="btn-secondary text-sm">
          <Globe size={14} /> My Websites
        </Link>
      </div>

      {result && (
        <div className={`flex items-start gap-3 px-4 py-3 rounded-lg text-sm ${
          result.success
            ? "bg-green-900/30 border border-green-700/50 text-green-300"
            : "bg-red-900/30 border border-red-700/50 text-red-300"
        }`}>
          {result.success ? <CheckCircle size={18} className="flex-shrink-0 mt-0.5" /> : <XCircle size={18} className="flex-shrink-0 mt-0.5" />}
          <div className="flex-1 min-w-0">
            <p className="font-medium">{result.message}</p>
            {result.success && (
              <div className="mt-2 space-y-1 text-xs text-green-400/80">
                {result.admin_url && (
                  <p>Admin: <a href={result.admin_url} target="_blank" rel="noopener noreferrer" className="underline hover:text-green-300">{result.admin_url}</a></p>
                )}
                {result.admin_user && <p>Username: <code className="bg-black/30 px-1.5 py-0.5 rounded">{result.admin_user}</code></p>}
                {result.admin_pass && <p>Password: <code className="bg-black/30 px-1.5 py-0.5 rounded">{result.admin_pass}</code></p>}
                {result.database && (
                  <div className="mt-2 bg-black/20 rounded p-2">
                    <p className="font-medium mb-1">Database Info:</p>
                    <p>DB: {result.database.database} | User: {result.database.username} | Host: {result.database.host}</p>
                    <p>Password: <code className="bg-black/30 px-1.5 py-0.5 rounded">{result.database.password}</code></p>
                  </div>
                )}
                {result.needs_web_setup && (
                  <p className="mt-2 text-yellow-300/80">
                    WP-CLI tidak tersedia. Buka website untuk setup WordPress melalui web installer.
                  </p>
                )}
              </div>
            )}
          </div>
          <button onClick={() => setResult(null)} className="opacity-60 hover:opacity-100 flex-shrink-0">X</button>
        </div>
      )}

      {/* Select Site */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white mb-3">1. Pilih Website</h3>
        <select
          value={selectedSite}
          onChange={(e) => {
            setSelectedSite(e.target.value);
            setResult(null);
            if (selectedApp) {
              const defaults: Record<string, string> = {};
              selectedApp.fields.forEach(f => {
                defaults[f.key] = f.default.replace("{domain}", e.target.value || "mysite.com");
              });
              setFormData(defaults);
            }
          }}
          className="input w-full"
        >
          <option value="">-- Pilih website untuk install --</option>
          {activeSites.map(s => (
            <option key={s.domain} value={s.domain}>{s.domain}</option>
          ))}
          {activeSites.length === 0 && sites.filter(s => s.exists).length > 0 && (
            <option disabled value="">Semua website sudah terinstall WordPress</option>
          )}
          {sites.filter(s => s.exists).length === 0 && (
            <option disabled value="">Tidak ada website tersedia</option>
          )}
        </select>
      </div>

      {/* Installed WordPress Sites */}
      {wpSites.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-white mb-3">
            <CheckCircle size={16} className="inline mr-1 text-blue-400" />
            WordPress Terinstall ({wpSites.length})
          </h3>
          <div className="space-y-2">
            {wpSites.map(s => (
              <div key={s.domain} className="flex items-center justify-between p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <div className="flex items-center gap-2 min-w-0">
                  <Code size={18} className="text-blue-400 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-white text-sm font-medium truncate">{s.domain}</p>
                    <p className="text-xs text-surface-400">
                      <a href={`https://${s.domain}/wp-admin`} target="_blank" className="hover:text-blue-400 underline">
                        wp-admin
                      </a>
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <a href={`https://${s.domain}`} target="_blank" rel="noopener noreferrer" className="btn-ghost text-xs">
                    <ExternalLink size={12} />
                  </a>
                  <button onClick={() => handleRemoveWP(s.domain)} className="btn-ghost text-xs text-red-400 hover:text-red-300">
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* App Catalog */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white mb-1">2. Pilih Aplikasi</h3>
        <p className="text-xs text-surface-500 mb-4">Klik aplikasi untuk melihat detail dan mulai instalasi</p>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={24} className="animate-spin text-brand-400" />
            <span className="ml-3 text-surface-400">Loading apps...</span>
          </div>
        ) : (
          <div className="space-y-6">
            {categories.map(cat => (
              <div key={cat}>
                <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">
                  {getCategoryLabel(cat)}
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {apps.filter(a => a.category === cat).map(app => (
                    <button
                      key={app.id}
                      onClick={() => handleSelectApp(app)}
                      className={`text-left p-4 rounded-lg border transition-all duration-200 ${
                        selectedApp?.id === app.id
                          ? "border-brand-500 bg-brand-500/10 ring-1 ring-brand-500/30"
                          : "border-surface-700 bg-surface-900 hover:border-surface-600 hover:bg-surface-800"
                      }`}
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <div
                          className="w-10 h-10 rounded-lg flex items-center justify-center text-white"
                          style={{ backgroundColor: app.color + "30", color: app.color }}
                        >
                          {getAppIcon(app)}
                        </div>
                        <div className="min-w-0">
                          <p className="text-white font-medium text-sm">{app.name}</p>
                          <p className="text-xs text-surface-500">v{app.version}</p>
                        </div>
                        {expandedApp === app.id ? (
                          <ChevronUp size={16} className="ml-auto text-surface-400" />
                        ) : (
                          <ChevronDown size={16} className="ml-auto text-surface-400" />
                        )}
                      </div>
                      <p className="text-xs text-surface-400 leading-relaxed">{app.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Install Form */}
      {selectedApp && expandedApp === selectedApp.id && (
        <div className="card border-brand-500/30">
          <div className="flex items-center gap-3 mb-4">
            <div
              className="w-12 h-12 rounded-lg flex items-center justify-center text-white"
              style={{ backgroundColor: selectedApp.color + "30", color: selectedApp.color }}
            >
              {getAppIcon(selectedApp)}
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">
                Install {selectedApp.name}
              </h3>
              <p className="text-xs text-surface-400">{selectedApp.description}</p>
            </div>
          </div>

          {!selectedSite ? (
            <div className="text-center py-8">
              <Globe size={32} className="mx-auto text-surface-700 mb-3" />
              <p className="text-surface-400 text-sm">Pilih website terlebih dahulu di atas</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-surface-800 rounded-lg p-3">
                <p className="text-xs text-surface-500 mb-1">Target website:</p>
                <p className="text-brand-400 font-medium">{selectedSite}</p>
              </div>

              {selectedApp.fields.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-white">Configuration</h4>
                  {selectedApp.fields.map(field => (
                    <div key={field.key}>
                      <label className="block text-xs font-medium text-surface-300 mb-1">
                        {field.label} {field.required && <span className="text-red-400">*</span>}
                      </label>
                      <input
                        type={field.type === "password" ? "password" : field.type === "email" ? "email" : "text"}
                        value={formData[field.key] || ""}
                        onChange={e => setFormData(prev => ({ ...prev, [field.key]: e.target.value }))}
                        className="input w-full"
                        placeholder={field.required ? `${field.label} wajib diisi` : "Otomatis digenerate"}
                      />
                    </div>
                  ))}
                  {selectedApp.id === "wordpress" && (
                    <p className="text-xs text-surface-500">
                      Kosongkan password untuk auto-generate password aman.
                    </p>
                  )}
                </div>
              )}

              {selectedApp.fields.length === 0 && (
                <p className="text-xs text-surface-400">
                  Tidak ada konfigurasi tambahan. Aplikasi akan di-download dan di-extract ke website.
                  Setup lanjutan dilakukan melalui web installer.
                </p>
              )}

              <button
                onClick={handleInstall}
                disabled={installing || !selectedSite}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-brand-500 hover:bg-brand-600 disabled:bg-brand-500/50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
              >
                {installing ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Installing {selectedApp.name}...
                  </>
                ) : (
                  <>
                    <Download size={18} />
                    Install {selectedApp.name} ke {selectedSite}
                  </>
                )}
              </button>

              {installing && (
                <div className="space-y-2">
                  <div className="w-full bg-surface-800 rounded-full h-2">
                    <div className="bg-brand-500 h-2 rounded-full animate-pulse" style={{ width: "60%" }} />
                  </div>
                  <p className="text-xs text-surface-400 text-center animate-pulse">
                    Downloading & configuring {selectedApp.name}...
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Info Card */}
      <div className="card bg-surface-900/50">
        <h4 className="text-sm font-medium text-white mb-2 flex items-center gap-2">
          <Shield size={16} className="text-brand-400" />
          Tentang App Installer
        </h4>
        <div className="text-xs text-surface-400 space-y-2">
          <p>
            ZaydPanel App Installer memungkinkan Anda install aplikasi populer dengan satu klik.
            Sistem akan otomatis mendownload, mengekstrak, membuat database, dan mengkonfigurasi permission.
          </p>
          <p>
            <strong className="text-surface-300">WordPress</strong> — Full auto-install. Database + wp-config.php + admin account dibuat otomatis.
            Jika WP-CLI tersedia di server, setup WordPress 100% otomatis tanpa perlu web installer.
          </p>
          <p>
            <strong className="text-surface-300">Aplikasi lain</strong> — File di-download dan di-extract. Database dibuat otomatis.
            Lanjutkan setup melalui web installer di browser.
          </p>
          <p>
            Simpan informasi database dan login admin yang ditampilkan setelah instalasi selesai.
          </p>
        </div>
      </div>
    </div>
  );
}
