"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { HardDrive, Search, Download, RotateCcw } from "lucide-react";
import Link from "next/link";

export default function LogsPage() {
  const [domain, setDomain] = useState("");
  const [logType, setLogType] = useState<"access" | "error">("access");
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [lines, setLines] = useState(100);
  const [search, setSearch] = useState("");

  const fetchLogs = async () => {
    if (!domain) return;
    setLoading(true);
    const res = await api.getLogs(domain, logType, lines);
    if (res.success && res.data) {
      setLogs(res.data.logs.map(l => l.timestamp ? `[${l.timestamp}] [${l.level}] ${l.message}` : l.message));
    } else {
      setLogs(["Error: " + (res.error || "Failed to fetch logs")]);
    }
    setLoading(false);
  };

  const filtered = search ? logs.filter(l => l.toLowerCase().includes(search.toLowerCase())) : logs;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Log Viewer</h1>
        <p className="text-surface-400 text-sm mt-1">Lihat log Nginx access dan error per website</p>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="label">Domain</label>
            <input
              type="text" value={domain} onChange={e => setDomain(e.target.value)}
              className="input" placeholder="example.com"
            />
          </div>
          <div>
            <label className="label">Log Type</label>
            <select value={logType} onChange={e => setLogType(e.target.value as "access" | "error")} className="input">
              <option value="access">Access Log</option>
              <option value="error">Error Log</option>
            </select>
          </div>
          <div>
            <label className="label">Lines</label>
            <select value={lines} onChange={e => setLines(Number(e.target.value))} className="input">
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={200}>200</option>
              <option value={500}>500</option>
            </select>
          </div>
          <div className="flex items-end">
            <button onClick={fetchLogs} disabled={loading || !domain} className="btn-primary w-full">
              <HardDrive size={14} /> View Logs
            </button>
          </div>
        </div>
      </div>

      {/* Search */}
      {logs.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2">
            <Search size={16} className="text-surface-400" />
            <input
              type="text" value={search} onChange={e => setSearch(e.target.value)}
              className="input flex-1" placeholder="Search logs..."
            />
            {search && <span className="text-xs text-surface-500">{filtered.length} of {logs.length} lines</span>}
          </div>
        </div>
      )}

      {/* Log Output */}
      <div className="card">
        {loading ? (
          <div className="flex items-center gap-2 py-4 text-surface-500">
            <RotateCcw size={14} className="animate-spin" /> Loading logs...
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12">
            <HardDrive size={48} className="mx-auto text-surface-700 mb-4" />
            <p className="text-surface-400 text-sm">Masukkan domain dan klik &quot;View Logs&quot; untuk melihat log.</p>
          </div>
        ) : (
          <div className="bg-surface-950 rounded-lg border border-surface-800 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 bg-surface-900 border-b border-surface-800">
              <span className="text-xs text-surface-400">{domain} - {logType} log ({filtered.length} lines)</span>
              <button onClick={() => { const b = new Blob([filtered.join("\n")], { type: "text/plain" }); const a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = `${domain}-${logType}.log`; a.click(); }} className="btn-ghost text-xs">
                <Download size={12} /> Download
              </button>
            </div>
            <div className="overflow-auto max-h-[60vh]">
              <pre className="text-xs font-mono p-4 text-surface-300 whitespace-pre-wrap">
                {filtered.map((line, i) => (
                  <div key={i} className={`py-0.5 ${line.toLowerCase().includes("error") || line.toLowerCase().includes("warn") ? "text-red-400" : ""}`}>
                    {line}
                  </div>
                ))}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
