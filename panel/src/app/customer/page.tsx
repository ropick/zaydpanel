"use client";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { api, type SiteInfo, type SSLInfo, type DatabaseInfo } from "@/lib/api";
import {
  Globe, Database, Lock, HardDrive, RefreshCw, Zap, ExternalLink,
  ArrowRight
} from "lucide-react";
import Link from "next/link";

export default function CustomerDashboard() {
  const { user } = useAuth();
  const [sites, setSites] = useState<SiteInfo[]>([]);
  const [sslCerts, setSslCerts] = useState<SSLInfo[]>([]);
  const [databases, setDatabases] = useState<DatabaseInfo[]>([]);
  const [quota, setQuota] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [sitesRes, sslRes, dbRes, quotaRes] = await Promise.all([
        api.listSites(),
        api.listSSL(),
        api.listDatabases(),
        api.getQuota(),
      ]);
      if (sitesRes.success) setSites(sitesRes.data || []);
      if (sslRes.success) setSslCerts(sslRes.data || []);
      if (dbRes.success) setDatabases(dbRes.data || []);
      if (quotaRes.success) setQuota(quotaRes.data);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const diskUsed = quota?.disk_used || "-";
  const diskTotal = quota?.disk_limit || "-";

  const stats = [
    { label: "My Websites", value: sites.length, icon: Globe, color: "bg-blue-500/20", textColor: "text-blue-400" },
    { label: "My Databases", value: databases.length, icon: Database, color: "bg-purple-500/20", textColor: "text-purple-400" },
    { label: "My SSL Certs", value: sslCerts.length, icon: Lock, color: "bg-green-500/20", textColor: "text-green-400" },
    { label: "Disk Used", value: diskUsed, sub: `/ ${diskTotal}`, icon: HardDrive, color: "bg-cyan-500/20", textColor: "text-cyan-400" },
  ];

  return (
    <div>
      {/* Welcome */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">
          Welcome, {user?.full_name || user?.username}
        </h1>
        <p className="text-surface-400 mt-1">Manage your websites and services</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((s) => (
          <div key={s.label} className="card">
            <div className="flex items-center gap-3 mb-3">
              <div className={`w-10 h-10 rounded-lg ${s.color} flex items-center justify-center`}>
                <s.icon size={20} className={s.textColor} />
              </div>
              <p className="text-surface-400 text-sm">{s.label}</p>
            </div>
            <p className="text-3xl font-bold text-white">{s.value}</p>
            {s.sub && <p className="text-surface-500 text-xs mt-1">{s.sub}</p>}
          </div>
        ))}
      </div>

      {/* Quota Info */}
      {quota && (
        <div className="card mb-6">
          <h3 className="text-sm font-semibold text-white mb-4">Resource Usage</h3>
          <div className="space-y-4">
            {quota.disk_limit && (
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-surface-400">Disk Space</span>
                  <span className="text-white">{quota.disk_used} / {quota.disk_limit}</span>
                </div>
                <div className="w-full bg-surface-800 rounded-full h-2">
                  <div className="bg-brand-500 h-2 rounded-full transition-all" style={{ width: `${Math.min(((parseFloat(quota.disk_used) || 0) / (parseFloat(quota.disk_limit) || 1)) * 100, 100)}%` }} />
                </div>
              </div>
            )}
            {quota.sites_limit !== undefined && (
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-surface-400">Websites</span>
                  <span className="text-white">{sites.length} / {quota.sites_limit}</span>
                </div>
                <div className="w-full bg-surface-800 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full transition-all" style={{ width: `${Math.min((sites.length / (quota.sites_limit || 1)) * 100, 100)}%` }} />
                </div>
              </div>
            )}
            {quota.databases_limit !== undefined && (
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-surface-400">Databases</span>
                  <span className="text-white">{databases.length} / {quota.databases_limit}</span>
                </div>
                <div className="w-full bg-surface-800 rounded-full h-2">
                  <div className="bg-purple-500 h-2 rounded-full transition-all" style={{ width: `${Math.min((databases.length / (quota.databases_limit || 1)) * 100, 100)}%` }} />
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <div className="card">
          <h3 className="text-sm font-semibold text-white mb-3">Quick Actions</h3>
          <div className="space-y-2">
            {sites.filter(s => s.exists && !s.has_wp).slice(0, 3).map((site) => (
              <div key={site.domain} className="flex items-center justify-between p-3 bg-surface-900 rounded-lg">
                <div className="flex items-center gap-2 min-w-0">
                  <Zap size={14} className="text-brand-400 flex-shrink-0" />
                  <span className="text-sm text-white truncate">{site.domain}</span>
                </div>
                <span className="text-xs text-surface-500">WordPress Available</span>
              </div>
            ))}
            {sites.filter(s => s.exists && !s.has_wp).length === 0 && (
              <p className="text-surface-500 text-sm py-2">No sites available for WordPress install</p>
            )}
          </div>
        </div>
        <div className="card">
          <h3 className="text-sm font-semibold text-white mb-3">SSL Status</h3>
          <div className="space-y-2">
            {sites.filter(s => s.exists && !s.ssl).slice(0, 3).map((site) => (
              <div key={site.domain} className="flex items-center justify-between p-3 bg-surface-900 rounded-lg">
                <div className="flex items-center gap-2 min-w-0">
                  <Lock size={14} className="text-yellow-400 flex-shrink-0" />
                  <span className="text-sm text-white truncate">{site.domain}</span>
                </div>
                <Link href="/customer/ssl" className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1">
                  Issue SSL <ArrowRight size={10} />
                </Link>
              </div>
            ))}
            {sites.filter(s => s.exists && !s.ssl).length === 0 && (
              <p className="text-surface-500 text-sm py-2">All sites have SSL certificates</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent Websites */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-white">My Websites</h3>
          <div className="flex gap-2">
            <button onClick={fetchData} disabled={loading} className="btn-ghost text-xs">
              <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Refresh
            </button>
            <Link href="/customer/sites" className="btn-primary text-xs">Manage</Link>
          </div>
        </div>
        {loading ? (
          <div className="animate-pulse text-surface-500 text-sm">Loading...</div>
        ) : sites.length === 0 ? (
          <div className="text-center py-8">
            <Globe size={48} className="mx-auto text-surface-700 mb-4" />
            <p className="text-surface-400 text-sm">No websites found. Contact your administrator to get started.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sites.map((site) => (
              <div key={site.domain} className="flex items-center justify-between p-3 bg-surface-900 rounded-lg">
                <div className="flex items-center gap-3 min-w-0">
                  <Globe size={16} className="text-brand-500 flex-shrink-0" />
                  <div className="min-w-0">
                    <span className="text-sm text-white font-medium">{site.domain}</span>
                    {site.ssl && <Lock size={12} className="inline text-green-400 ml-2" />}
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
                  <a href={`https://${site.domain}`} target="_blank" rel="noopener noreferrer" className="btn-ghost text-xs p-1.5" title="Visit">
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
