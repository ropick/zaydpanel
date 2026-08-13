"use client";
import { useState, useEffect } from "react";
import { api, type PHPVersion } from "@/lib/api";
import { Code, RefreshCw, CheckCircle, ArrowRight } from "lucide-react";

export default function PHPPage() {
  const [versions, setVersions] = useState<PHPVersion[]>([]);
  const [sites, setSites] = useState<{ domain: string; php_version?: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<string | null>(null);
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null);

  const fetchData = async () => {
    setLoading(true);
    const [phpRes, sitesRes] = await Promise.all([api.listPHPVersions(), api.listSites()]);
    if (phpRes.success) setVersions(phpRes.data || []);
    if (sitesRes.success) setSites(sitesRes.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleSetVersion = async (domain: string, version: string) => {
    setAction(`${domain}-${version}`);
    setResult(null);
    const res = await api.setPHPVersion(domain, version);
    setResult({ success: !!res.success, msg: res.success ? `${domain} berhasil diubah ke PHP ${version}!` : (res.error || "Gagal") });
    setAction(null);
    if (res.success) fetchData();
  };

  const activeVersion = versions.find(v => v.active);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">PHP Manager</h1>
          <p className="text-surface-400 text-sm mt-1">Kelola versi PHP untuk setiap website</p>
        </div>
        <button onClick={fetchData} disabled={loading} className="btn-secondary">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      {result && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${result.success ? "bg-brand-900/30 border border-brand-800/50 text-brand-400" : "bg-red-900/30 border border-red-800/50 text-red-400"}`}>
          {result.success ? "✓" : "✗"} {result.msg}
          <button onClick={() => setResult(null)} className="ml-auto opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      {/* Available Versions */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Code size={18} className="text-purple-400" />
          <h3 className="text-sm font-semibold text-white">Versi PHP Tersedia</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {versions.map((v) => (
            <div key={v.version} className={`p-3 rounded-lg border ${v.active ? "bg-brand-600/20 border-brand-600/30" : "bg-surface-900 border-surface-800"}`}>
              <div className="flex items-center gap-2">
                <span className="text-white font-bold">PHP {v.version}</span>
                {v.active && <CheckCircle size={14} className="text-brand-400" />}
              </div>
              <p className="text-xs text-surface-500 mt-1">{v.path}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Per-Site PHP Version */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <ArrowRight size={18} className="text-surface-400" />
          <h3 className="text-sm font-semibold text-white">PHP Version per Website</h3>
        </div>
        {loading ? (
          <div className="animate-pulse text-surface-500">Loading...</div>
        ) : sites.length === 0 ? (
          <p className="text-surface-500 text-sm">Belum ada website.</p>
        ) : (
          <div className="space-y-3">
            {sites.map((site) => (
              <div key={site.domain} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-surface-900 rounded-lg">
                <div>
                  <span className="text-sm text-white font-medium">{site.domain}</span>
                  <p className="text-xs text-surface-500">Current: PHP {site.php_version || activeVersion?.version || "-"}</p>
                </div>
                <div className="flex gap-2 flex-wrap">
                  {versions.map((v) => (
                    <button
                      key={v.version}
                      onClick={() => handleSetVersion(site.domain, v.version)}
                      disabled={action === `${site.domain}-${v.version}`}
                      className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-all ${
                        site.php_version === v.version
                          ? "bg-brand-600 text-white"
                          : "bg-surface-800 text-surface-300 hover:bg-surface-700 hover:text-white"
                      }`}
                    >
                      {v.version}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
