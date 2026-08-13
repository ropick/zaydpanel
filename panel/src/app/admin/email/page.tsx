"use client";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import {
  Mail as MailIcon,
  RefreshCw,
  Plus,
  Trash2,
  X,
  Loader2,
  Search,
} from "lucide-react";

interface EmailAccount {
  id: number;
  domain: string;
  address: string;
  quota_mb: number;
  user_id?: number;
  created_at?: string;
}

const emptyForm = {
  domain: "",
  address: "",
  password: "",
  quota_mb: "500",
};

type ToastState = {
  success: boolean;
  msg: string;
} | null;

export default function AdminEmailPage() {
  const [emails, setEmails] = useState<EmailAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<ToastState>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...emptyForm });
  const [search, setSearch] = useState("");
  const [createdPassword, setCreatedPassword] = useState<string | null>(null);

  const fetchEmails = useCallback(async () => {
    setLoading(true);
    const res = await api.listEmail();
    if (res.success) setEmails(res.data || []);
    setLoading(false);
  }, []);

  useEffect(() => { fetchEmails(); }, [fetchEmails]);

  const showToast = (success: boolean, msg: string) => {
    setToast({ success, msg });
    setTimeout(() => setToast(null), 4000);
  };

  const openAddForm = () => {
    setForm({ ...emptyForm });
    setCreatedPassword(null);
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setCreatedPassword(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.domain.trim() || !form.address.trim()) return;
    setSubmitting(true);
    const res = await api.createEmail(form.domain.trim(), form.address.trim(), form.password.trim() || undefined, Number(form.quota_mb) || 500);
    if (res.success && res.data) {
      const d = res.data as Record<string, any>;
      setCreatedPassword(d?.password || "");
      showToast(true, `Email ${d?.address || form.address} created!`);
      setForm({ ...emptyForm, domain: form.domain });
      fetchEmails();
    } else {
      showToast(false, res.error || "Failed to create email");
    }
    setSubmitting(false);
  };

  const handleDelete = async (email: EmailAccount) => {
    if (!confirm(`Delete email "${email.address}@${email.domain}"?`)) return;
    const res = await api.deleteEmail(email.id);
    if (res.success) {
      showToast(true, `Email deleted`);
      fetchEmails();
    } else {
      showToast(false, res.error || "Failed");
    }
  };

  const filtered = search
    ? emails.filter((e) => e.address.toLowerCase().includes(search.toLowerCase()) || e.domain.toLowerCase().includes(search.toLowerCase()))
    : emails;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Email Manager</h1>
          <p className="text-surface-400 text-sm mt-1">Manage email accounts for all domains</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchEmails} disabled={loading} className="btn-secondary">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button onClick={openAddForm} className="btn-primary">
            <Plus size={14} /> Add Email
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <MailIcon size={18} className="text-brand-400" />
            <span className="text-surface-400 text-sm">Total Accounts</span>
          </div>
          <p className="text-2xl font-bold text-white">{emails.length}</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <MailIcon size={18} className="text-cyan-400" />
            <span className="text-surface-400 text-sm">Domains</span>
          </div>
          <p className="text-2xl font-bold text-white">{new Set(emails.map((e) => e.domain)).size}</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <MailIcon size={18} className="text-purple-400" />
            <span className="text-surface-400 text-sm">Total Quota</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {emails.reduce((acc, e) => acc + (e.quota_mb || 0), 0) >= 1024
              ? `${(emails.reduce((acc, e) => acc + (e.quota_mb || 0), 0) / 1024).toFixed(1)} GB`
              : `${emails.reduce((acc, e) => acc + (e.quota_mb || 0), 0)} MB`}
          </p>
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
            <h2 className="text-lg font-semibold text-white">Add New Email Account</h2>
            <button onClick={closeForm} className="btn-ghost p-2 text-surface-400 hover:text-white"><X size={16} /></button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Domain *</label>
                <input type="text" className="input" placeholder="e.g. example.com" value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })} required disabled={submitting} />
              </div>
              <div>
                <label className="label">Email Address *</label>
                <div className="flex items-center">
                  <input type="text" className="input rounded-r-none" placeholder="e.g. info" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} required disabled={submitting} />
                  {form.domain && <span className="px-3 py-2.5 bg-surface-800 border border-l-0 border-surface-700 text-surface-400 text-sm rounded-r-lg">@{form.domain}</span>}
                </div>
              </div>
              <div>
                <label className="label">Password (optional)</label>
                <input type="text" className="input" placeholder="Auto-generated if empty" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} disabled={submitting} />
              </div>
              <div>
                <label className="label">Quota (MB)</label>
                <input type="number" className="input" placeholder="500" min="1" value={form.quota_mb} onChange={(e) => setForm({ ...form, quota_mb: e.target.value })} disabled={submitting} />
              </div>
            </div>
            {createdPassword && (
              <div className="p-3 bg-yellow-900/20 border border-yellow-800/50 rounded-lg">
                <p className="text-yellow-400 text-sm font-medium">Generated Password (save this!):</p>
                <p className="text-white font-mono mt-1 select-all">{createdPassword}</p>
              </div>
            )}
            <div className="flex gap-2 pt-2">
              <button type="submit" disabled={submitting} className="btn-primary">
                {submitting && <Loader2 size={14} className="animate-spin" />} Create Email
              </button>
              <button type="button" onClick={closeForm} disabled={submitting} className="btn-secondary">Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <div className="flex items-center gap-2">
          <Search size={16} className="text-surface-400" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} className="input flex-1" placeholder="Search emails..." />
          {search && <span className="text-xs text-surface-500">{filtered.length} of {emails.length}</span>}
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="card animate-pulse h-16" />)}</div>
      ) : filtered.length === 0 ? (
        <div className="card text-center py-12">
          <MailIcon size={48} className="mx-auto text-surface-700 mb-4" />
          <h3 className="text-lg font-medium text-surface-300 mb-2">No email accounts</h3>
          <p className="text-surface-500 text-sm mb-4">Create the first email account</p>
          <button onClick={openAddForm} className="btn-primary"><Plus size={14} /> Add Email</button>
        </div>
      ) : (
        <div className="card !p-0 overflow-hidden">
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-700">
                  <th className="text-left text-surface-400 font-medium px-6 py-3">Email Address</th>
                  <th className="text-left text-surface-400 font-medium px-6 py-3">Quota</th>
                  <th className="text-left text-surface-400 font-medium px-6 py-3">Created</th>
                  <th className="text-right text-surface-400 font-medium px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((email) => (
                  <tr key={email.id} className="border-b border-surface-700/50 hover:bg-surface-700/30">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center"><MailIcon size={14} className="text-purple-400" /></div>
                        <span className="text-white font-medium">{email.address}@{email.domain}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-surface-300">{email.quota_mb} MB</td>
                    <td className="px-6 py-4 text-surface-400">{email.created_at ? new Date(email.created_at).toLocaleDateString("id-ID") : "—"}</td>
                    <td className="px-6 py-4 text-right">
                      <button onClick={() => handleDelete(email)} className="btn-ghost text-xs px-2.5 py-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/20"><Trash2 size={12} /> Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="md:hidden divide-y divide-surface-700/50">
            {filtered.map((email) => (
              <div key={email.id} className="p-4 space-y-2">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-500/20 rounded-full flex items-center justify-center"><MailIcon size={16} className="text-purple-400" /></div>
                  <div>
                    <p className="text-white font-medium text-sm">{email.address}@{email.domain}</p>
                    <p className="text-surface-500 text-xs">{email.quota_mb} MB quota</p>
                  </div>
                </div>
                <div className="flex justify-end">
                  <button onClick={() => handleDelete(email)} className="btn-ghost text-xs px-3 py-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/20"><Trash2 size={12} /> Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
