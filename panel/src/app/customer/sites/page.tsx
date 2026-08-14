"use client";
import { useState, useEffect } from "react";
import { api, type SiteInfo } from "@/lib/api";
import { Globe, RefreshCw, ExternalLink, Lock, FileText, Zap, Search } from "lucide-react";
import Link from "next/link";

export default function CustomerSitesPage() {
  const [sites, setSites] = useState<SiteInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<string | null>(null);
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null);
  const [search, setSearch] = useState("");

  const fetchSites = async () => {
    setLoading(true);
    const res = await api.listSites();
    if (res.success) setSites(res.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchSites(); }, []);

  const handleInstallWP = async (domain: string) => {
    setAction(domain);
    const res = await api.installWordPress(domain, domain, "admin");
    setResult({
      success: !!res.success,
      msg: res.success ? `WordPress installed on ${domain}!` : (res.error || "Failed to install WordPress"),
    });
    setAction(null);
    if (res.success) fetchSites();
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
        <button onClick={fetchSites} disabled={loading} className="btn-secondary">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      {result && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${result.success ? "bg-brand-900/30 border border-brand-800/50 text-brand-400" : "bg-red-900/30 border border-red-800/50 text-red-400"}`}>
          {result.success ? "✓" : "✗"} {result.msg}
          <button onClick={() => setResult(null)} className="ml-auto opacity-60 hover:opacity-100">✕</button>
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
                  <div className="w-10 h-10 bg-brand-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Globe size={18} className="text-brand-400" />
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
                <div className="flex items-center gap-2 flex-shrink-0">
                  {site.has_wp && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-medium">WordPress</span>
                  )}
                  {site.exists ? (
                    <span className="text-xs px-2 py-0.5 rounded bg-brand-500/20 text-brand-400">Active</span>
                  ) : (
                    <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400">No Home</span>
                  )}
                  {!site.has_wp && site.exists && (
                    <button
                      onClick={() => handleInstallWP(site.domain)}
                      disabled={action === site.domain}
                      className="btn-ghost text-xs"
                      title="Install WordPress"
                    >
                      <Zap size={12} className={action === site.domain ? "animate-spin" : ""} /> WP
                    </button>
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
    </div>
  );
}
