"use client";
import { useState, useEffect } from "react";
import { api, type BackupInfo } from "@/lib/api";
import { HardDrive, RefreshCw, Download, Upload, Trash2, RotateCcw, Clock, Database } from "lucide-react";

export default function BackupsPage() {
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [sites, setSites] = useState<{ domain: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<string | null>(null);
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState("");

  const fetchData = async () => {
    setLoading(true);
    const [backupRes, sitesRes] = await Promise.all([api.listBackups(), api.listSites()]);
    if (backupRes.success) setBackups(backupRes.data || []);
    if (sitesRes.success) setSites(sitesRes.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = async () => {
    if (!selectedDomain) return;
    setAction("create");
    const res = await api.createBackup(selectedDomain);
    setResult({ success: !!res.success, msg: res.success ? `Backup ${selectedDomain} berhasil dibuat!` : (res.error || "Gagal") });
    setAction(null);
    setShowCreate(false);
    if (res.success) fetchData();
  };

  const handleRestore = async (id: string) => {
    if (!confirm("Restore backup ini? Data website akan dikembalikan ke saat backup dibuat.")) return;
    setAction(id);
    const res = await api.restoreBackup(id);
    setResult({ success: !!res.success, msg: res.success ? "Backup berhasil di-restore!" : (res.error || "Gagal") });
    setAction(null);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Hapus backup ini?")) return;
    setAction(id);
    const res = await api.deleteBackup(id);
    setResult({ success: !!res.success, msg: res.success ? "Backup dihapus." : (res.error || "Gagal") });
    setAction(null);
    if (res.success) fetchData();
  };

  const handleDownload = async (id: string) => {
    const res = await api.downloadBackup(id);
    if (res.success && res.data?.url) {
      window.open(res.data.url, "_blank");
    }
  };

  const totalSize = backups.reduce((acc, b) => {
    const num = parseFloat(b.size);
    return acc + (b.size.includes("GB") ? num * 1024 : num);
  }, 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Backups</h1>
          <p className="text-surface-400 text-sm mt-1">Backup dan restore website Anda</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchData} disabled={loading} className="btn-secondary">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button onClick={() => setShowCreate(!showCreate)} className="btn-primary">
            <Upload size={14} /> Buat Backup
          </button>
        </div>
      </div>

      {result && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${result.success ? "bg-brand-900/30 border border-brand-800/50 text-brand-400" : "bg-red-900/30 border border-red-800/50 text-red-400"}`}>
          {result.success ? "✓" : "✗"} {result.msg}
          <button onClick={() => setResult(null)} className="ml-auto opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      {/* Create Backup */}
      {showCreate && (
        <div className="card">
          <h3 className="text-sm font-semibold text-white mb-4">Buat Backup Baru</h3>
          <div className="flex gap-3">
            <select value={selectedDomain} onChange={e => setSelectedDomain(e.target.value)} className="input flex-1">
              <option value="">Pilih domain...</option>
              {sites.map(s => <option key={s.domain} value={s.domain}>{s.domain}</option>)}
            </select>
            <button onClick={handleCreate} disabled={action === "create" || !selectedDomain} className="btn-primary">
              {action === "create" ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><Upload size={14} /> Backup</>}
            </button>
            <button onClick={() => setShowCreate(false)} className="btn-secondary">Batal</button>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <Database size={18} className="text-blue-400" />
            <span className="text-surface-400 text-sm">Total Backups</span>
          </div>
          <p className="text-2xl font-bold text-white">{backups.length}</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <HardDrive size={18} className="text-cyan-400" />
            <span className="text-surface-400 text-sm">Total Size</span>
          </div>
          <p className="text-2xl font-bold text-white">{totalSize > 1024 ? `${(totalSize / 1024).toFixed(1)} GB` : `${totalSize.toFixed(0)} MB`}</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <Clock size={18} className="text-purple-400" />
            <span className="text-surface-400 text-sm">Last Backup</span>
          </div>
          <p className="text-lg font-bold text-white">{backups[0]?.created_at || "-"}</p>
        </div>
      </div>

      {/* Backup List */}
      <div className="card">
        <h3 className="text-sm font-semibold text-white mb-4">Semua Backups</h3>
        {loading ? (
          <div className="animate-pulse text-surface-500">Loading...</div>
        ) : backups.length === 0 ? (
          <div className="text-center py-12">
            <HardDrive size={48} className="mx-auto text-surface-700 mb-4" />
            <h3 className="text-lg font-medium text-surface-300 mb-2">Belum ada backup</h3>
            <p className="text-surface-500 text-sm mb-4">Buat backup pertama untuk melindungi data website Anda</p>
          </div>
        ) : (
          <div className="space-y-3">
            {backups.map((backup) => (
              <div key={backup.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-surface-900 rounded-lg">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Database size={18} className="text-cyan-400" />
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-white font-medium truncate">{backup.domain}</h4>
                    <p className="text-xs text-surface-500">{backup.filename} &middot; {backup.size} &middot; {backup.created_at}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button onClick={() => handleDownload(backup.id)} className="btn-ghost text-xs" title="Download">
                    <Download size={12} />
                  </button>
                  <button onClick={() => handleRestore(backup.id)} disabled={action === backup.id} className="btn-ghost text-xs text-yellow-400 hover:text-yellow-300 hover:bg-yellow-900/20" title="Restore">
                    <RotateCcw size={12} className={action === backup.id ? "animate-spin" : ""} /> Restore
                  </button>
                  <button onClick={() => handleDelete(backup.id)} disabled={action === backup.id} className="btn-ghost text-xs text-red-400 hover:text-red-300 hover:bg-red-900/20" title="Delete">
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
