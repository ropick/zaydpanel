"use client";
import { useState, useEffect } from "react";
import { api, type SystemSetting } from "@/lib/api";
import { Settings, RefreshCw, Save, Server, Globe, Clock, Zap } from "lucide-react";

export default function SettingsPage() {
  const [settings, setSettings] = useState<SystemSetting[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null);
  const [edits, setEdits] = useState<Record<string, string>>({});

  const fetchSettings = async () => {
    setLoading(true);
    const res = await api.getSettings();
    if (res.success) setSettings(res.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchSettings(); }, []);

  const handleSave = async (key: string) => {
    const value = edits[key];
    if (value === undefined) return;
    setSaving(key);
    const res = await api.updateSetting(key, value);
    setResult({ success: !!res.success, msg: res.success ? `${key} berhasil diperbarui!` : (res.error || "Gagal") });
    setSaving(null);
    setEdits(prev => { const n = { ...prev }; delete n[key]; return n; });
    if (res.success) fetchSettings();
  };

  const grouped = settings.reduce<Record<string, SystemSetting[]>>((acc, s) => {
    const group = s.key.split("_")[0] || "other";
    if (!acc[group]) acc[group] = [];
    acc[group].push(s);
    return acc;
  }, {});

  const groupIcons: Record<string, React.ReactNode> = {
    server: <Server size={16} className="text-surface-400" />,
    system: <Zap size={16} className="text-yellow-400" />,
    hostname: <Globe size={16} className="text-blue-400" />,
    timezone: <Clock size={16} className="text-purple-400" />,
    security: <Zap size={16} className="text-red-400" />,
  };

  const groupLabels: Record<string, string> = {
    server: "Server", system: "System", hostname: "Hostname",
    timezone: "Timezone", security: "Security", other: "Other",
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          <p className="text-surface-400 text-sm mt-1">Pengaturan panel dan server</p>
        </div>
        <button onClick={fetchSettings} disabled={loading} className="btn-secondary">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      {result && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${result.success ? "bg-brand-900/30 border border-brand-800/50 text-brand-400" : "bg-red-900/30 border border-red-800/50 text-red-400"}`}>
          {result.success ? "✓" : "✗"} {result.msg}
          <button onClick={() => setResult(null)} className="ml-auto opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      {/* Settings Groups */}
      {loading ? (
        <div className="animate-pulse text-surface-500">Loading settings...</div>
      ) : settings.length === 0 ? (
        <div className="card text-center py-12">
          <Settings size={48} className="mx-auto text-surface-700 mb-4" />
          <p className="text-surface-400 text-sm">Belum ada konfigurasi. Agent perlu diupdate untuk mendukung settings.</p>
        </div>
      ) : (
        Object.entries(grouped).map(([group, items]) => (
          <div key={group} className="card">
            <div className="flex items-center gap-2 mb-4">
              {groupIcons[group] || <Settings size={16} className="text-surface-400" />}
              <h3 className="text-sm font-semibold text-white">{groupLabels[group] || group}</h3>
            </div>
            <div className="space-y-4">
              {items.map((setting) => (
                <div key={setting.key} className="flex flex-col sm:flex-row sm:items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white">{setting.key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</p>
                    <p className="text-xs text-surface-500">{setting.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      defaultValue={setting.value}
                      onChange={e => setEdits(prev => ({ ...prev, [setting.key]: e.target.value }))}
                      className="input w-64 font-mono text-sm"
                    />
                    <button
                      onClick={() => handleSave(setting.key)}
                      disabled={saving === setting.key}
                      className="btn-primary text-xs"
                    >
                      {saving === setting.key ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><Save size={12} /> Save</>}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}

      {/* Panel Info */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <Settings size={18} className="text-brand-400" />
          <h3 className="text-sm font-semibold text-white">Panel Info</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="flex justify-between p-3 bg-surface-900 rounded-lg">
            <span className="text-surface-500">Panel Version</span>
            <span className="text-white font-medium">v2.1</span>
          </div>
          <div className="flex justify-between p-3 bg-surface-900 rounded-lg">
            <span className="text-surface-500">Framework</span>
            <span className="text-white font-medium">Next.js 15 + React 19</span>
          </div>
          <div className="flex justify-between p-3 bg-surface-900 rounded-lg">
            <span className="text-surface-500">Panel URL</span>
            <span className="text-brand-400 font-medium">https://panel.pro99.my.id</span>
          </div>
          <div className="flex justify-between p-3 bg-surface-900 rounded-lg">
            <span className="text-surface-500">Agent Port</span>
            <span className="text-white font-medium">8442 (Internal)</span>
          </div>
        </div>
      </div>
    </div>
  );
}


