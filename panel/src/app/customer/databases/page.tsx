"use client";
import { useState, useEffect } from "react";
import { api, type DatabaseInfo } from "@/lib/api";
import { Database, RefreshCw, Search, ExternalLink } from "lucide-react";

export default function CustomerDatabasesPage() {
  const [databases, setDatabases] = useState<DatabaseInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const fetchDatabases = async () => {
    setLoading(true);
    const res = await api.listDatabases();
    if (res.success) setDatabases(res.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchDatabases(); }, []);

  const filtered = search
    ? databases.filter((d) => d.name.toLowerCase().includes(search.toLowerCase()))
    : databases;

  const totalSize = databases.reduce((acc, d) => {
    const num = parseFloat(d.size);
    return acc + (d.size.includes("GB") ? num * 1024 : num);
  }, 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">My Databases</h1>
          <p className="text-surface-400 text-sm mt-1">View your MySQL databases</p>
        </div>
        <button onClick={fetchDatabases} disabled={loading} className="btn-secondary">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <Database size={18} className="text-purple-400" />
            <span className="text-surface-400 text-sm">Total Databases</span>
          </div>
          <p className="text-2xl font-bold text-white">{databases.length}</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <Database size={18} className="text-cyan-400" />
            <span className="text-surface-400 text-sm">Total Size</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {totalSize > 1024 ? `${(totalSize / 1024).toFixed(1)} GB` : `${totalSize.toFixed(0)} MB`}
          </p>
        </div>
      </div>

      {/* Search + List */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Search size={16} className="text-surface-400" />
          <input
            type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            className="input flex-1" placeholder="Search databases..."
          />
          {search && <span className="text-xs text-surface-500">{filtered.length} of {databases.length}</span>}
        </div>

        {loading ? (
          <div className="animate-pulse text-surface-500">Loading databases...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12">
            <Database size={48} className="mx-auto text-surface-700 mb-4" />
            <h3 className="text-lg font-medium text-surface-300 mb-2">No databases found</h3>
            <p className="text-surface-500 text-sm">Your databases will appear here once created by the administrator.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map((db) => (
              <div key={db.name} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-surface-900 rounded-lg">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Database size={18} className="text-purple-400" />
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-white font-medium font-mono">{db.name}</h4>
                    <div className="flex items-center gap-3 text-xs text-surface-500 mt-1">
                      <span>User: {db.user}</span>
                      <span>Size: {db.size}</span>
                      {db.domain && <span>Domain: {db.domain}</span>}
                    </div>
                  </div>
                </div>
                <a href="/phpmyadmin" target="_blank" className="btn-ghost text-xs flex-shrink-0" title="Open phpMyAdmin">
                  <ExternalLink size={12} /> phpMyAdmin
                </a>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
