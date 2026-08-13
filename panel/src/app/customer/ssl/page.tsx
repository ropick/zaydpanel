"use client";
import { useState, useEffect } from "react";
import { api, type SSLInfo } from "@/lib/api";
import { Lock, RefreshCw, Shield, AlertTriangle, CheckCircle, Plus } from "lucide-react";

export default function CustomerSSLPage() {
  const [certs, setCerts] = useState<SSLInfo[]>([]);
  const [sites, setSites] = useState<{ domain: string; ssl?: boolean }[]>([]);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<string | null>(null);
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null);

  const fetchData = async () => {
    setLoading(true);
    const [sslRes, sitesRes] = await Promise.all([api.listSSL(), api.listSites()]);
    if (sslRes.success) setCerts(sslRes.data || []);
    if (sitesRes.success) setSites(sitesRes.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleIssue = async (domain: string) => {
    setAction(domain);
    setResult(null);
    const res = await api.issueSSL(domain);
    setResult({
      success: !!res.success,
      msg: res.success ? `SSL issued for ${domain}!` : (res.error || "Failed to issue SSL"),
    });
    setAction(null);
    if (res.success) fetchData();
  };

  const domainsWithoutSSL = sites.filter((s) => !certs.find((c) => c.domain === s.domain));

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">SSL Certificates</h1>
          <p className="text-surface-400 text-sm mt-1">Manage SSL for your websites</p>
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

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <Shield size={18} className="text-brand-400" />
            <span className="text-surface-400 text-sm">Total Certificates</span>
          </div>
          <p className="text-2xl font-bold text-white">{certs.length}</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <CheckCircle size={18} className="text-green-400" />
            <span className="text-surface-400 text-sm">Active</span>
          </div>
          <p className="text-2xl font-bold text-white">{certs.filter((c) => c.days_left > 30).length}</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle size={18} className="text-yellow-400" />
            <span className="text-surface-400 text-sm">Expiring Soon</span>
          </div>
          <p className="text-2xl font-bold text-white">{certs.filter((c) => c.days_left <= 30).length}</p>
        </div>
      </div>

      {/* Certificate List */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white mb-4">My Certificates</h3>
        {loading ? (
          <div className="animate-pulse text-surface-500">Loading...</div>
        ) : certs.length === 0 ? (
          <div className="text-center py-8">
            <Lock size={48} className="mx-auto text-surface-700 mb-4" />
            <p className="text-surface-400 text-sm">No SSL certificates found.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {certs.map((cert) => (
              <div key={cert.domain} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-surface-900 rounded-lg">
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${cert.days_left > 30 ? "bg-green-500/20" : cert.days_left > 7 ? "bg-yellow-500/20" : "bg-red-500/20"}`}>
                    <Lock size={18} className={cert.days_left > 30 ? "text-green-400" : cert.days_left > 7 ? "text-yellow-400" : "text-red-400"} />
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-white font-medium truncate">{cert.domain}</h4>
                    <p className="text-xs text-surface-500">{cert.issuer} &middot; {cert.type}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className="text-right">
                    <p className={`text-sm font-medium ${cert.days_left > 30 ? "text-green-400" : cert.days_left > 7 ? "text-yellow-400" : "text-red-400"}`}>
                      {cert.days_left} days
                    </p>
                    <p className="text-xs text-surface-500">Expires: {cert.expires_at}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Issue new SSL */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white mb-4">Issue New Certificate</h3>
        {domainsWithoutSSL.length === 0 ? (
          <p className="text-surface-500 text-sm">All your websites have SSL certificates.</p>
        ) : (
          <div className="space-y-2">
            {domainsWithoutSSL.map((s) => (
              <div key={s.domain} className="flex items-center justify-between p-3 bg-surface-900 rounded-lg">
                <span className="text-sm text-white">{s.domain}</span>
                <button
                  onClick={() => handleIssue(s.domain)}
                  disabled={action === s.domain}
                  className="btn-primary text-xs"
                >
                  {action === s.domain ? (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <><Plus size={12} /> Issue SSL</>
                  )}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
