"use client";
import { useState, useEffect } from "react";
import { api, type CronJob } from "@/lib/api";
import { ListChecks, Plus, Trash2, RefreshCw, Clock, ToggleLeft, ToggleRight, AlertCircle } from "lucide-react";

export default function CronPage() {
  const [crons, setCrons] = useState<CronJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null);
  const [form, setForm] = useState({ domain: "", schedule: "* * * * *", command: "", description: "" });
  const [action, setAction] = useState<string | null>(null);

  const fetchCrons = async () => {
    setLoading(true);
    const res = await api.listCronJobs();
    if (res.success) setCrons(res.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchCrons(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setAction("create");
    const res = await api.createCronJob(form.domain, form.schedule, form.command, form.description);
    setResult({ success: !!res.success, msg: res.success ? "Cron job berhasil dibuat!" : (res.error || "Gagal") });
    setAction(null);
    if (res.success) {
      setShowForm(false);
      setForm({ domain: "", schedule: "* * * * *", command: "", description: "" });
      fetchCrons();
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Hapus cron job ini?")) return;
    setAction(id);
    const res = await api.deleteCronJob(id);
    setResult({ success: !!res.success, msg: res.success ? "Cron job dihapus." : (res.error || "Gagal") });
    setAction(null);
    if (res.success) fetchCrons();
  };

  const handleToggle = async (id: string, enabled: boolean) => {
    setAction(id);
    const res = await api.toggleCronJob(id, enabled);
    if (res.success) fetchCrons();
    setAction(null);
  };

  const presets = [
    { label: "Setiap menit", value: "* * * * *" },
    { label: "Setiap 5 menit", value: "*/5 * * * *" },
    { label: "Setiap jam", value: "0 * * * *" },
    { label: "Setiap hari (00:00)", value: "0 0 * * *" },
    { label: "Setiap minggu", value: "0 0 * * 0" },
    { label: "Setiap bulan", value: "0 0 1 * *" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Cron Jobs</h1>
          <p className="text-surface-400 text-sm mt-1">Kelola tugas terjadwal di server</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchCrons} disabled={loading} className="btn-secondary">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary">
            <Plus size={14} /> Tambah Cron
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
      {showForm && (
        <div className="card">
          <h3 className="text-sm font-semibold text-white mb-4">Buat Cron Job Baru</h3>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Domain</label>
                <input type="text" value={form.domain} onChange={e => setForm({ ...form, domain: e.target.value })} className="input" placeholder="example.com" required />
              </div>
              <div>
                <label className="label">Schedule (Cron Expression)</label>
                <div className="flex gap-2">
                  <input type="text" value={form.schedule} onChange={e => setForm({ ...form, schedule: e.target.value })} className="input flex-1 font-mono" required />
                </div>
              </div>
            </div>
            {/* Presets */}
            <div>
              <label className="label">Preset</label>
              <div className="flex flex-wrap gap-2">
                {presets.map((p) => (
                  <button key={p.value} type="button" onClick={() => setForm({ ...form, schedule: p.value })} className={`text-xs px-3 py-1.5 rounded-lg font-mono transition-all ${form.schedule === p.value ? "bg-brand-600 text-white" : "bg-surface-800 text-surface-300 hover:bg-surface-700"}`}>
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="label">Command</label>
              <input type="text" value={form.command} onChange={e => setForm({ ...form, command: e.target.value })} className="input font-mono" placeholder="/usr/bin/php /home/user/public_html/cron.php" required />
            </div>
            <div>
              <label className="label">Deskripsi (opsional)</label>
              <input type="text" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} className="input" placeholder="Deskripsi tugas" />
            </div>
            <div className="flex gap-2">
              <button type="submit" disabled={action === "create" || !form.domain || !form.command} className="btn-primary">
                {action === "create" ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><Plus size={14} /> Buat Cron Job</>}
              </button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Batal</button>
            </div>
          </form>
        </div>
      )}

      {/* Cron List */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <ListChecks size={18} className="text-surface-400" />
          <h3 className="text-sm font-semibold text-white">Semua Cron Jobs ({crons.length})</h3>
        </div>
        {loading ? (
          <div className="animate-pulse text-surface-500">Loading...</div>
        ) : crons.length === 0 ? (
          <div className="text-center py-12">
            <Clock size={48} className="mx-auto text-surface-700 mb-4" />
            <h3 className="text-lg font-medium text-surface-300 mb-2">Belum ada cron job</h3>
            <p className="text-surface-500 text-sm mb-4">Buat cron job pertama untuk menjalankan tugas terjadwal</p>
          </div>
        ) : (
          <div className="space-y-3">
            {crons.map((cron) => (
              <div key={cron.id} className={`p-4 rounded-lg border ${cron.enabled ? "bg-surface-900 border-surface-800" : "bg-surface-950 border-surface-800 opacity-60"}`}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-white font-medium">{cron.description || cron.command}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${cron.enabled ? "bg-green-500/20 text-green-400" : "bg-surface-800 text-surface-500"}`}>
                        {cron.enabled ? "Enabled" : "Disabled"}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-surface-500">
                      <span className="font-mono">{cron.schedule}</span>
                      <span>{cron.domain}</span>
                      <code className="bg-surface-800 px-2 py-0.5 rounded text-surface-400">{cron.command}</code>
                    </div>
                    {cron.next_run && (
                      <p className="text-xs text-surface-600 mt-1">Next run: {cron.next_run}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => handleToggle(cron.id, !cron.enabled)}
                      disabled={action === cron.id}
                      className="btn-ghost text-xs"
                      title={cron.enabled ? "Disable" : "Enable"}
                    >
                      {cron.enabled ? <ToggleRight size={16} className="text-brand-400" /> : <ToggleLeft size={16} className="text-surface-500" />}
                    </button>
                    <button
                      onClick={() => handleDelete(cron.id)}
                      disabled={action === cron.id}
                      className="btn-ghost text-xs text-red-400 hover:text-red-300 hover:bg-red-900/20"
                    >
                      <Trash2 size={14} /> Hapus
                    </button>
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
