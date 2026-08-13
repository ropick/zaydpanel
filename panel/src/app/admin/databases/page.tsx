"use client";
import { useState, useEffect, useCallback } from "react";
import { api, FileItem, type DatabaseInfo } from "@/lib/api";
import { Database, Plus, Trash2, RefreshCw, ExternalLink, Search } from "lucide-react";

export default function DatabasesPage() {
  const [databases, setDatabases] = useState<DatabaseInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [createDomain, setCreateDomain] = useState("");
  const [action, setAction] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const fetchDatabases = async () => {
    setLoading(true);
    const res = await api.listDatabases();
    if (res.success) setDatabases(res.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchDatabases(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setAction("create");
    const res = await api.createDatabase(createDomain);
    setResult({ success: !!res.success, msg: res.success ? `Database untuk ${createDomain} berhasil dibuat!` : (res.error || "Gagal") });
    setAction(null);
    if (res.success) { setShowCreate(false); setCreateDomain(""); fetchDatabases(); }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Hapus database "${name}"? Semua data akan hilang permanen.`)) return;
    setAction(name);
    const res = await api.deleteDatabase(name);
    setResult({ success: !!res.success, msg: res.success ? "Database berhasil dihapus!" : (res.error || "Gagal") });
    setAction(null);
    if (res.success) fetchDatabases();
  };

  const filtered = search ? databases.filter(d => d.name.toLowerCase().includes(search.toLowerCase())) : databases;
  const totalSize = databases.reduce((acc, d) => {
    const num = parseFloat(d.size);
    return acc + (d.size.includes("GB") ? num * 1024 : num);
  }, 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Databases</h1>
          <p className="text-surface-400 text-sm mt-1">Kelola database MySQL</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchDatabases} disabled={loading} className="btn-secondary">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button onClick={() => setShowCreate(!showCreate)} className="btn-primary">
            <Plus size={14} /> Buat Database
          </button>
        </div>
      </div>

      {result && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${result.success ? "bg-brand-900/30 border border-brand-800/50 text-brand-400" : "bg-red-900/30 border border-red-800/50 text-red-400"}`}>
          {result.success ? "✓" : "✗"} {result.msg}
          <button onClick={() => setResult(null)} className="ml-auto opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      {/* Create Form */}
      {showCreate && (
        <div className="card">
          <h3 className="text-sm font-semibold text-white mb-4">Buat Database Baru</h3>
          <form onSubmit={handleCreate} className="flex gap-3">
            <input type="text" value={createDomain} onChange={e => setCreateDomain(e.target.value)} className="input flex-1" placeholder="Domain (contoh: example.com)" required />
            <button type="submit" disabled={action === "create" || !createDomain} className="btn-primary">
              {action === "create" ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><Plus size={14} /> Buat</>}
            </button>
            <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Batal</button>
          </form>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <Database size={18} className="text-blue-400" />
            <span className="text-surface-400 text-sm">Total Databases</span>
          </div>
          <p className="text-2xl font-bold text-white">{databases.length}</p>
        </div>
        <div className="card">
          <span className="text-surface-400 text-sm">Total Size</span>
          <p className="text-2xl font-bold text-white mt-2">{totalSize > 1024 ? `${(totalSize / 1024).toFixed(1)} GB` : `${totalSize.toFixed(0)} MB`}</p>
        </div>
        <div className="card">
          <span className="text-surface-400 text-sm">phpMyAdmin</span>
          <p className="mt-2">
            <a href="/phpmyadmin" target="_blank" className="btn-ghost text-xs">
              <ExternalLink size={12} /> Buka phpMyAdmin
            </a>
          </p>
        </div>
      </div>

      {/* Database List */}
      <div className="card">
        {/* Search */}
        <div className="flex items-center gap-2 mb-4">
          <Search size={16} className="text-surface-400" />
          <input type="text" value={search} onChange={e => setSearch(e.target.value)} className="input flex-1" placeholder="Cari database..." />
          {search && <span className="text-xs text-surface-500">{filtered.length} of {databases.length}</span>}
        </div>

        {loading ? (
          <div className="animate-pulse text-surface-500">Loading databases...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12">
            <Database size={48} className="mx-auto text-surface-700 mb-4" />
            <h3 className="text-lg font-medium text-surface-300 mb-2">Belum ada database</h3>
            <p className="text-surface-500 text-sm mb-4">Buat database pertama untuk website Anda</p>
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map((db) => (
              <div key={db.name} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-surface-900 rounded-lg">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Database size={18} className="text-blue-400" />
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
                <button onClick={() => handleDelete(db.name)} disabled={action === db.name} className="btn-ghost text-xs text-red-400 hover:text-red-300 hover:bg-red-900/20 flex-shrink-0">
                  <Trash2 size={12} /> Hapus
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
