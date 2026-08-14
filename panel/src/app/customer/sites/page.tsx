"use client";
import { useState, useEffect } from "react";
import { api, type SiteInfo } from "@/lib/api";
import {
  Globe, RefreshCw, ExternalLink, Lock, FileText, Zap, Search,
  X, CheckCircle, XCircle, Loader2, Eye, EyeOff, Code,
} from "lucide-react";
import Link from "next/link";

export default function CustomerSitesPage() {
  const [sites, setSites] = useState<SiteInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showWPModal, setShowWPModal] = useState<string | null>(null);
  const [installing, setInstalling] = useState(false);
  const [wpTitle, setWpTitle] = useState("");
  const [wpAdminUser, setWpAdminUser] = useState("admin");
  const [wpAdminPass, setWpAdminPass] = useState("");
  const [wpAdminEmail, setWpAdminEmail] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [result, setResult] = useState<{ success: boolean; msg: string; details?: any } | null>(null);

  const fetchSites = async () => {
    setLoading(true);
    const res = await api.listSites();
    if (res.success) setSites(res.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchSites(); }, []);

  const openWPModal = (domain: string) => {
    setShowWPModal(domain);
    setWpTitle(domain);
    setWpAdminUser("admin");
    setWpAdminPass("");
    setWpAdminEmail(`admin@${domain}`);
    setResult(null);
  };

  const handleInstallWP = async () => {
    if (!showWPModal) return;
    setInstalling(true);
    setResult(null);
    const res = await api.installWordPress(showWPModal, wpTitle, wpAdminUser, wpAdminPass || "", wpAdminEmail);
    setInstalling(false);
    if (res.success && res.data) {
      const d = res.data as any;
      setResult({
        success: true,
        msg: `WordPress berhasil diinstall di ${showWPModal}!`,
        details: d,
      });
      fetchSites();
    } else {
      setResult({
        success: false,
        msg: (res as any).error || "Gagal install WordPress",
      });
    }
  };

  const filtered = search
    ? sites.filter((s) => s.domain.toLowerCase().includes(search.toLowerCase()))
    : sites;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">My Websites</h1>
          <p className="text-surface-400 text-sm mt-1">View and manage your websites</p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/customer/apps" className="btn-primary text-sm">
            <Zap size={14} /> Install App
          </Link>
          <button onClick={fetchSites} disabled={loading} className="btn-secondary">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>
      </div>

      {/* Global Result */}
      {result && !showWPModal && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${
          result.success ? "bg-brand-900/30 border border-brand-800/50 text-brand-400" : "bg-red-900/30 border border-red-800/50 text-red-400"
        }`}>
          {result.success ? <CheckCircle size={16} /> : <XCircle size={16} />}
          {result.msg}
          <button onClick={() => setResult(null)} className="ml-auto opacity-60 hover:opacity-100">X</button>
        </div>
      )}

      {/* Search */}
      <div className="card">
        <div className="flex items-center gap-2">
          <Search size={16} className="text-surface-400" />
          <input
            type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            className="input flex-1" placeholder="Search websites..."
          />
          {search && <span className="text-xs text-surface-500">{filtered.length} of {sites.length}</span>}
        </div>
      </div>

      {/* Site List */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white mb-4">Websites ({filtered.length})</h3>
        {loading ? (
          <div className="animate-pulse text-surface-500">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12">
            <Globe size={48} className="mx-auto text-surface-700 mb-4" />
            <h3 className="text-lg font-medium text-surface-300 mb-2">No websites found</h3>
            <p className="text-surface-500 text-sm">Contact your administrator to add websites.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map((site) => (
              <div key={site.domain} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-surface-900 rounded-lg">
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    site.has_wp ? "bg-blue-500/20" : "bg-brand-500/20"
                  }`}>
                    {site.has_wp ? <Code size={18} className="text-blue-400" /> : <Globe size={18} className="text-brand-400" />}
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-white font-medium truncate">{site.domain}</h4>
                    <div className="flex items-center gap-3 text-xs text-surface-500 mt-1">
                      <span>Home: {site.home || "-"}</span>
                      {site.php_version && <span>PHP {site.php_version}</span>}
                      {site.ssl && <span className="text-green-400">SSL Active</span>}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
                  {site.has_wp ? (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-medium flex items-center gap-1">
                      <Code size={12} /> WordPress
                    </span>
                  ) : site.exists ? (
                    <button
                      onClick={() => openWPModal(site.domain)}
                      className="text-xs px-2.5 py-1 rounded bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 font-medium flex items-center gap-1 transition-colors"
                      title="Install WordPress"
                    >
                      <Zap size={12} /> Install WP
                    </button>
                  ) : (
                    <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400">No Home</span>
                  )}
                  <Link href="/customer/ssl" className="btn-ghost text-xs" title="SSL">
                    <Lock size={12} />
                  </Link>
                  <Link
                    href={`/customer/sites/${site.domain}/files`}
                    className="btn-ghost text-xs"
                    title="File Manager"
                  >
                    <FileText size={12} />
                  </Link>
                  <a
                    href={`https://${site.domain}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-ghost text-xs"
                    title="Visit site"
                  >
                    <ExternalLink size={12} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* WordPress Install Modal */}
      {showWPModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-surface-900 border border-surface-700 rounded-xl max-w-md w-full shadow-2xl">
            <div className="flex items-center justify-between p-4 border-b border-surface-800">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                  <Code size={20} className="text-blue-400" />
                </div>
                <div>
                  <h3 className="text-white font-bold">Install WordPress</h3>
                  <p className="text-xs text-surface-400">{showWPModal}</p>
                </div>
              </div>
              <button onClick={() => { setShowWPModal(null); setResult(null); }} className="text-surface-400 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <div className="p-4 space-y-3">
              {result && (
                <div className={`flex items-start gap-2 px-3 py-2 rounded-lg text-xs ${
                  result.success ? "bg-green-900/30 border border-green-700/50 text-green-300" : "bg-red-900/30 border border-red-700/50 text-red-300"
                }`}>
                  {result.success ? <CheckCircle size={14} className="flex-shrink-0 mt-0.5" /> : <XCircle size={14} className="flex-shrink-0 mt-0.5" />}
                  <div>
                    <p className="font-medium">{result.msg}</p>
                    {result.success && result.details && (
                      <div className="mt-1 space-y-0.5">
                        {result.details.admin_url && <p>Admin: <a href={result.details.admin_url} target="_blank" className="underline">{result.details.admin_url}</a></p>}
                        {result.details.admin_user && <p>User: <code className="bg-black/30 px-1 rounded">{result.details.admin_user}</code></p>}
                        {result.details.admin_pass && <p>Pass: <code className="bg-black/30 px-1 rounded">{result.details.admin_pass}</code></p>}
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">Site Title</label>
                <input
                  type="text" value={wpTitle} onChange={e => setWpTitle(e.target.value)}
                  className="input w-full" placeholder="My Awesome Website"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">Admin Username</label>
                <input
                  type="text" value={wpAdminUser} onChange={e => setWpAdminUser(e.target.value)}
                  className="input w-full" placeholder="admin"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">Admin Password</label>
                <div className="relative">
                  <input
                    type={showPass ? "text" : "password"} value={wpAdminPass} onChange={e => setWpAdminPass(e.target.value)}
                    className="input w-full pr-10" placeholder="Leave empty for auto-generate"
                  />
                  <button onClick={() => setShowPass(!showPass)} className="absolute right-2 top-1/2 -translate-y-1/2 text-surface-400 hover:text-white">
                    {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
                <p className="text-xs text-surface-500 mt-1">Kosongkan untuk auto-generate password aman</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-surface-300 mb-1">Admin Email</label>
                <input
                  type="email" value={wpAdminEmail} onChange={e => setWpAdminEmail(e.target.value)}
                  className="input w-full" placeholder={`admin@${showWPModal}`}
                />
              </div>

              <button
                onClick={handleInstallWP}
                disabled={installing}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-500/50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors text-sm"
              >
                {installing ? (
                  <><Loader2 size={16} className="animate-spin" /> Installing WordPress...</>
                ) : (
                  <><Zap size={16} /> Install WordPress</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
