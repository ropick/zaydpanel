"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { FolderOpen, RefreshCw, Search, Plus, X, Loader2 } from "lucide-react";

interface FTPAccount {
  id: number;
  domain: string;
  username: string;
  home_dir: string;
  created_at?: string;
}

export default function CustomerFTPPage() {
  const [accounts, setAccounts] = useState<FTPAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ domain: "", username: "", password: "", home_dir: "" });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null);
  const [createdPwd, setCreatedPwd] = useState<string | null>(null);

  const fetchAccounts = async () => {
    setLoading(true);
    const res = await api.listFTP();
    if (res.success) setAccounts(res.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchAccounts(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.domain.trim() || !form.username.trim()) return;
    setSubmitting(true);
    setResult(null);
    const res = await api.createFTP(form.domain.trim(), form.username.trim(), form.password.trim() || undefined, form.home_dir.trim() || undefined);
    if (res.success && res.data) {
      const d = res.data as Record<string, any>;
      setResult({ success: true, msg: `FTP user "${d?.username || form.username}" created!` });
      setCreatedPwd(d?.password || null);
      setForm({ domain: form.domain, username: "", password: "", home_dir: "" });
      fetchAccounts();
    } else {
      setResult({ success: false, msg: res.error || "Failed" });
    }
    setSubmitting(false);
  };

  const filtered = search ? accounts.filter((a) => a.username.toLowerCase().includes(search.toLowerCase()) || a.domain.toLowerCase().includes(search.toLowerCase())) : accounts;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">My FTP Accounts</h1>
          <p className="text-surface-400 text-sm mt-1">Manage FTP access to your sites</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchAccounts} disabled={loading} className="btn-secondary">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button onClick={() => { setShowForm(!showForm); setResult(null); setCreatedPwd(null); }} className="btn-primary">
            <Plus size={14} /> Add FTP
          </button>
        </div>
      </div>

      {result && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${result.success ? "bg-brand-900/30 border border-brand-800/50 text-brand-400" : "bg-red-900/30 border border-red-800/50 text-red-400"}`}>
          {result.success ? "✓" : "✗"} {result.msg}
          <button onClick={() => setResult(null)} className="ml-auto opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      {showForm && (
        <div className="card border-brand-700/50">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Add New FTP Account</h2>
            <button onClick={() => setShowForm(false)} className="btn-ghost p-2 text-surface-400 hover:text-white"><X size={16} /></button>
          </div>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Domain *</label>
                <input type="text" className="input" placeholder="e.g. example.com" value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })} required disabled={submitting} />
              </div>
              <div>
                <label className="label">FTP Username *</label>
                <input type="text" className="input font-mono" placeholder="e.g. myuser" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "") })} required disabled={submitting} />
                <p className="text-xs text-surface-500 mt-1">Full: {form.username || "user"}_{form.domain ? form.domain.replace(".", "_") : "domain"}</p>
              </div>
              <div>
                <label className="label">Password (optional)</label>
                <input type="text" className="input" placeholder="Auto-generated" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} disabled={submitting} />
              </div>
              <div>
                <label className="label">Home Directory</label>
                <input type="text" className="input font-mono" placeholder="/home/domain (auto)" value={form.home_dir} onChange={(e) => setForm({ ...form, home_dir: e.target.value })} disabled={submitting} />
              </div>
            </div>
            {createdPwd && (
              <div className="p-3 bg-yellow-900/20 border border-yellow-800/50 rounded-lg">
                <p className="text-yellow-400 text-sm font-medium">Generated Password (save this!):</p>
                <p className="text-white font-mono mt-1 select-all">{createdPwd}</p>
              </div>
            )}
            <div className="flex gap-2">
              <button type="submit" disabled={submitting} className="btn-primary">{submitting && <Loader2 size={14} className="animate-spin" />} Create FTP</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <div className="flex items-center gap-2">
          <Search size={16} className="text-surface-400" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} className="input flex-1" placeholder="Search FTP accounts..." />
        </div>
      </div>

      <div className="card">
        <h3 className="text-sm font-semibold text-white mb-4">FTP Accounts ({filtered.length})</h3>
        {loading ? (
          <div className="animate-pulse text-surface-500">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12">
            <FolderOpen size={48} className="mx-auto text-surface-700 mb-4" />
            <p className="text-surface-400 text-sm">No FTP accounts found</p>
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map((account) => (
              <div key={account.id} className="flex items-center justify-between p-4 bg-surface-900 rounded-lg">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FolderOpen size={18} className="text-cyan-400" />
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-white font-medium font-mono">{account.username}</h4>
                    <p className="text-xs text-surface-500">{account.domain} — {account.home_dir}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
