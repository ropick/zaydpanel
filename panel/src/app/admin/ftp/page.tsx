"use client";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import {
  FolderOpen as FolderIcon,
  RefreshCw,
  Plus,
  Trash2,
  X,
  Loader2,
  Search,
} from "lucide-react";

interface FTPAccount {
  id: number;
  domain: string;
  username: string;
  home_dir: string;
  user_id?: number;
  created_at?: string;
}

const emptyForm = { domain: "", username: "", password: "", home_dir: "" };
type ToastState = { success: boolean; msg: string } | null;

export default function AdminFTPPage() {
  const [accounts, setAccounts] = useState<FTPAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<ToastState>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...emptyForm });
  const [search, setSearch] = useState("");
  const [createdPassword, setCreatedPassword] = useState<string | null>(null);

  const fetchAccounts = useCallback(async () => {
    setLoading(true);
    const res = await api.listFTP();
    if (res.success) setAccounts(res.data || []);
    setLoading(false);
  }, []);

  useEffect(() => { fetchAccounts(); }, [fetchAccounts]);

  const showToast = (success: boolean, msg: string) => {
    setToast({ success, msg });
    setTimeout(() => setToast(null), 4000);
  };

  const openAddForm = () => { setForm({ ...emptyForm }); setCreatedPassword(null); setShowForm(true); };
  const closeForm = () => { setShowForm(false); setCreatedPassword(null); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.domain.trim() || !form.username.trim()) return;
    setSubmitting(true);
    const res = await api.createFTP(form.domain.trim(), form.username.trim(), form.password.trim() || undefined, form.home_dir.trim() || undefined);
    if (res.success && res.data) {
      const d = res.data as Record<string, any>;
      setCreatedPassword(d?.password || "");
      showToast(true, `FTP user "${d?.username || form.username}" created!`);
      setForm({ ...emptyForm, domain: form.domain });
      fetchAccounts();
    } else {
      showToast(false, res.error || "Failed to create FTP account");
    }
    setSubmitting(false);
  };

  const handleDelete = async (account: FTPAccount) => {
    if (!confirm(`Delete FTP user "${account.username}"?`)) return;
    const res = await api.deleteFTP(account.id);
    if (res.success) { showToast(true, "FTP account deleted"); fetchAccounts(); }
    else { showToast(false, res.error || "Failed"); }
  };

  const filtered = search ? accounts.filter((a) => a.username.toLowerCase().includes(search.toLowerCase()) || a.domain.toLowerCase().includes(search.toLowerCase())) : accounts;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">FTP Manager</h1>
          <p className="text-surface-400 text-sm mt-1">Manage FTP accounts for file access</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchAccounts} disabled={loading} className="btn-secondary">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button onClick={openAddForm} className="btn-primary"><Plus size={14} /> Add FTP</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <div className="flex items-center gap-3 mb-2"><FolderIcon size={18} className="text-brand-400" /><span className="text-surface-400 text-sm">Total Accounts</span></div>
          <p className="text-2xl font-bold text-white">{accounts.length}</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 mb-2"><FolderIcon size={18} className="text-cyan-400" /><span className="text-surface-400 text-sm">Domains</span></div>
          <p className="text-2xl font-bold text-white">{new Set(accounts.map((a) => a.domain)).size}</p>
        </div>
      </div>

      {toast && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${toast.success ? "bg-brand-900/30 border border-brand-800/50 text-brand-400" : "bg-red-900/30 border border-red-800/50 text-red-400"}`}>
          {toast.success ? "✓" : "✗"} {toast.msg}
          <button onClick={() => setToast(null)} className="ml-auto opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      {showForm && (
        <div className="card border-brand-700/50">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Add New FTP Account</h2>
            <button onClick={closeForm} className="btn-ghost p-2 text-surface-400 hover:text-white"><X size={16} /></button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
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
                <input type="text" className="input" placeholder="Auto-generated if empty" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} disabled={submitting} />
              </div>
              <div>
                <label className="label">Home Directory</label>
                <input type="text" className="input font-mono" placeholder="/home/domain (auto)" value={form.home_dir} onChange={(e) => setForm({ ...form, home_dir: e.target.value })} disabled={submitting} />
              </div>
            </div>
            {createdPassword && (
              <div className="p-3 bg-yellow-900/20 border border-yellow-800/50 rounded-lg">
                <p className="text-yellow-400 text-sm font-medium">Generated Password (save this!):</p>
                <p className="text-white font-mono mt-1 select-all">{createdPassword}</p>
              </div>
            )}
            <div className="flex gap-2 pt-2">
              <button type="submit" disabled={submitting} className="btn-primary">{submitting && <Loader2 size={14} className="animate-spin" />} Create FTP Account</button>
              <button type="button" onClick={closeForm} disabled={submitting} className="btn-secondary">Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <div className="flex items-center gap-2">
          <Search size={16} className="text-surface-400" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} className="input flex-1" placeholder="Search FTP accounts..." />
          {search && <span className="text-xs text-surface-500">{filtered.length} of {accounts.length}</span>}
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="card animate-pulse h-16" />)}</div>
      ) : filtered.length === 0 ? (
        <div className="card text-center py-12">
          <FolderIcon size={48} className="mx-auto text-surface-700 mb-4" />
          <h3 className="text-lg font-medium text-surface-300 mb-2">No FTP accounts</h3>
          <p className="text-surface-500 text-sm mb-4">Create the first FTP account</p>
          <button onClick={openAddForm} className="btn-primary"><Plus size={14} /> Add FTP</button>
        </div>
      ) : (
        <div className="card !p-0 overflow-hidden">
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-700">
                  <th className="text-left text-surface-400 font-medium px-6 py-3">Username</th>
                  <th className="text-left text-surface-400 font-medium px-6 py-3">Domain</th>
                  <th className="text-left text-surface-400 font-medium px-6 py-3">Home Dir</th>
                  <th className="text-right text-surface-400 font-medium px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((account) => (
                  <tr key={account.id} className="border-b border-surface-700/50 hover:bg-surface-700/30">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-cyan-500/20 rounded-full flex items-center justify-center"><FolderIcon size={14} className="text-cyan-400" /></div>
                        <span className="text-white font-mono text-sm">{account.username}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-surface-300">{account.domain}</td>
                    <td className="px-6 py-4 text-surface-400 font-mono text-xs">{account.home_dir}</td>
                    <td className="px-6 py-4 text-right">
                      <button onClick={() => handleDelete(account)} className="btn-ghost text-xs px-2.5 py-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/20"><Trash2 size={12} /> Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="md:hidden divide-y divide-surface-700/50">
            {filtered.map((account) => (
              <div key={account.id} className="p-4 space-y-2">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center"><FolderIcon size={16} className="text-cyan-400" /></div>
                  <div>
                    <p className="text-white font-mono text-sm">{account.username}</p>
                    <p className="text-surface-500 text-xs">{account.home_dir}</p>
                  </div>
                </div>
                <div className="flex justify-end">
                  <button onClick={() => handleDelete(account)} className="btn-ghost text-xs px-3 py-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/20"><Trash2 size={12} /> Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
