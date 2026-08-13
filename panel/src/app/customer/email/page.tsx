"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Mail, RefreshCw, Search, Plus, X, Loader2 } from "lucide-react";

interface EmailAccount {
  id: number;
  domain: string;
  address: string;
  quota_mb: number;
  created_at?: string;
}

export default function CustomerEmailPage() {
  const [emails, setEmails] = useState<EmailAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ domain: "", address: "", password: "", quota_mb: "500" });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null);
  const [createdPwd, setCreatedPwd] = useState<string | null>(null);

  const fetchEmails = async () => {
    setLoading(true);
    const res = await api.listEmail();
    if (res.success) setEmails(res.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchEmails(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.domain.trim() || !form.address.trim()) return;
    setSubmitting(true);
    setResult(null);
    const res = await api.createEmail(form.domain.trim(), form.address.trim(), form.password.trim() || undefined, Number(form.quota_mb) || 500);
    if (res.success && res.data) {
      const d = res.data as Record<string, any>;
      setResult({ success: true, msg: `Email ${d?.address || form.address} created!` });
      setCreatedPwd(d?.password || null);
      setForm({ domain: form.domain, address: "", password: "", quota_mb: "500" });
      fetchEmails();
    } else {
      setResult({ success: false, msg: res.error || "Failed" });
    }
    setSubmitting(false);
  };

  const filtered = search ? emails.filter((e) => e.address.toLowerCase().includes(search.toLowerCase()) || e.domain.toLowerCase().includes(search.toLowerCase())) : emails;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">My Email Accounts</h1>
          <p className="text-surface-400 text-sm mt-1">Manage email accounts for your domains</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchEmails} disabled={loading} className="btn-secondary">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button onClick={() => { setShowForm(!showForm); setResult(null); setCreatedPwd(null); }} className="btn-primary">
            <Plus size={14} /> Add Email
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
            <h2 className="text-lg font-semibold text-white">Add New Email Account</h2>
            <button onClick={() => setShowForm(false)} className="btn-ghost p-2 text-surface-400 hover:text-white"><X size={16} /></button>
          </div>
          <form onSubmit={handleCreate} className="space-y-4">
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
                <input type="text" className="input" placeholder="Auto-generated" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} disabled={submitting} />
              </div>
              <div>
                <label className="label">Quota (MB)</label>
                <input type="number" className="input" placeholder="500" min="1" value={form.quota_mb} onChange={(e) => setForm({ ...form, quota_mb: e.target.value })} disabled={submitting} />
              </div>
            </div>
            {createdPwd && (
              <div className="p-3 bg-yellow-900/20 border border-yellow-800/50 rounded-lg">
                <p className="text-yellow-400 text-sm font-medium">Password (save this!):</p>
                <p className="text-white font-mono mt-1 select-all">{createdPwd}</p>
              </div>
            )}
            <div className="flex gap-2">
              <button type="submit" disabled={submitting} className="btn-primary">{submitting && <Loader2 size={14} className="animate-spin" />} Create Email</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <div className="flex items-center gap-2">
          <Search size={16} className="text-surface-400" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} className="input flex-1" placeholder="Search emails..." />
        </div>
      </div>

      <div className="card">
        <h3 className="text-sm font-semibold text-white mb-4">Email Accounts ({filtered.length})</h3>
        {loading ? (
          <div className="animate-pulse text-surface-500">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12">
            <Mail size={48} className="mx-auto text-surface-700 mb-4" />
            <p className="text-surface-400 text-sm">No email accounts found</p>
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map((email) => (
              <div key={email.id} className="flex items-center justify-between p-4 bg-surface-900 rounded-lg">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Mail size={18} className="text-purple-400" />
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-white font-medium">{email.address}@{email.domain}</h4>
                    <p className="text-xs text-surface-500">Quota: {email.quota_mb} MB</p>
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
