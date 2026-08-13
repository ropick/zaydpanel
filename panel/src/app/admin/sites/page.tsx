"use client";
import { useEffect, useState } from "react";
import { api, type SiteInfo } from "@/lib/api";
import { Globe, RefreshCw, Plus, ExternalLink, FolderOpen, Lock, Trash2, Database } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function SitesPage() {
  const [sites, setSites] = useState<SiteInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<{ domain: string; type: string } | null>(null);
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null);
  const router = useRouter();

  const fetchSites = async () => {
    setLoading(true);
    const res = await api.listSites();
    if (res.success) setSites(res.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchSites(); }, []);

  const handleAction = async (type: string, domain: string) => {
    setAction({ domain, type }); setResult(null);
    let res;
    switch (type) {
      case "delete":
        if (!confirm(`Hapus website ${domain}?\nSemua data akan dihapus permanen.`)) { setAction(null); return; }
        res = await api.deleteSite(domain); break;
      case "wordpress":
        res = await api.installWordPress(domain, domain, "admin", "", ""); break;
      case "ssl":
        res = await api.issueSSL(domain); break;
      default:
        res = { success: false, error: "Unknown action" };
    }
    setResult({ success: !!res.success, msg: res.success ? "Berhasil!" : (res.error || "Gagal") });
    setAction(null);
    if (res.success && type === "delete") fetchSites();
    if (res.success) fetchSites();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Websites</h1>
          <p className="text-surface-400 text-sm mt-1">Kelola semua website di server</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchSites} disabled={loading} className="btn-secondary">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <Link href="/admin/sites/create" className="btn-primary">
            <Plus size={14} /> Buat Website
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-surface-400 text-sm">Total Sites</p>
          <p className="text-2xl font-bold text-white">{sites.length}</p>
        </div>
        <div className="card">
          <p className="text-surface-400 text-sm">Active</p>
          <p className="text-2xl font-bold text-brand-400">{sites.filter(s => s.exists).length}</p>
        </div>
        <div className="card">
          <p className="text-surface-400 text-sm">With SSL</p>
          <p className="text-2xl font-bold text-green-400">{sites.filter(s => s.ssl).length}</p>
        </div>
        <div className="card">
          <p className="text-surface-400 text-sm">WordPress</p>
          <p className="text-2xl font-bold text-blue-400">{sites.filter(s => s.has_wp).length}</p>
        </div>
      </div>

      {result && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${result.success ? "bg-brand-900/30 border border-brand-800/50 text-brand-400" : "bg-red-900/30 border border-red-800/50 text-red-400"}`}>
          {result.success ? "✓" : "✗"} {result.msg}
          <button onClick={() => setResult(null)} className="ml-auto opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      {/* Sites List */}
      {loading ? (
        <div className="space-y-3">{[1, 2, 3].map(i => <div key={i} className="card animate-pulse h-28" />)}</div>
      ) : sites.length === 0 ? (
        <div className="card text-center py-12">
          <Globe size={48} className="mx-auto text-surface-700 mb-4" />
          <h3 className="text-lg font-medium text-surface-300 mb-2">Belum ada website</h3>
          <p className="text-surface-500 text-sm mb-4">Mulai dengan membuat website pertama Anda</p>
          <Link href="/admin/sites/create" className="btn-primary"><Plus size={14} /> Buat Website Baru</Link>
        </div>
      ) : (
        <div className="grid gap-3">
          {sites.map(site => (
            <div key={site.domain} className="card">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                {/* Left: Site info */}
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-12 h-12 bg-surface-700 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Globe size={20} className={site.exists ? "text-brand-400" : "text-red-400"} />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-white font-medium">{site.domain}</h3>
                      <span className={site.exists ? "badge-green" : "badge-yellow"}>
                        {site.exists ? "Active" : "No Home"}
                      </span>
                      {site.type === 'proxy' && (
                        <span className="badge-blue">Proxy</span>
                      )}
                      {site.ssl && (
                        <span className="badge-green">
                          <Lock size={10} className="mr-1" /> SSL
                        </span>
                      )}
                      {site.has_wp && (
                        <span className="px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 text-xs font-medium">
                          WordPress
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-surface-500">
                      <span>{site.home}</span>
                      {site.php_version && <span className="font-mono">PHP {site.php_version}</span>}
                    </div>
                  </div>
                </div>

                {/* Right: Actions */}
                <div className="flex items-center gap-2 flex-wrap">
                  <a href={`http${site.ssl ? "s" : ""}://${site.domain}`} target="_blank" rel="noopener noreferrer" className="btn-ghost text-xs">
                    <ExternalLink size={12} /> Visit
                  </a>
                  <button onClick={() => handleAction("wordpress", site.domain)} disabled={action?.domain === site.domain} className="btn-ghost text-xs" title="Install WordPress">
                    WordPress
                  </button>
                  <button onClick={() => handleAction("ssl", site.domain)} disabled={action?.domain === site.domain} className="btn-ghost text-xs" title="Issue SSL">
                    <Lock size={12} /> SSL
                  </button>
                  <Link href={`/admin/sites/${encodeURIComponent(site.domain)}/files`} className="btn-ghost text-xs">
                    <FolderOpen size={12} /> Files
                  </Link>
                  <button onClick={() => handleAction("delete", site.domain)} disabled={action?.domain === site.domain} className="btn-ghost text-xs text-red-400 hover:text-red-300 hover:bg-red-900/20">
                    <Trash2 size={12} /> Hapus
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
