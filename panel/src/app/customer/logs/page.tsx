"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { ScrollText, Search, Download, RotateCcw } from "lucide-react";

export default function CustomerLogsPage() {
  const [sites, setSites] = useState<{ domain: string }[]>([]);
  const [selectedDomain, setSelectedDomain] = useState("");
  const [logType, setLogType] = useState<"access" | "error">("access");
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [sitesLoading, setSitesLoading] = useState(true);
  const [lines, setLines] = useState(100);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const fetchSites = async () => {
      setSitesLoading(true);
      const res = await api.listSites();
      if (res.success && res.data) {
        setSites(res.data.filter((s) => s.exists));
      }
      setSitesLoading(false);
    };
    fetchSites();
  }, []);

  const fetchLogs = async () => {
    if (!selectedDomain) return;
    setLoading(true);
    const res = await api.getLogs(selectedDomain, logType, lines);
    if (res.success && res.data) {
      setLogs(res.data.logs.map((l) => (l.timestamp ? `[${l.timestamp}] [${l.level}] ${l.message}` : l.message)));
    } else {
      setLogs(["Error: " + (res.error || "Failed to fetch logs")]);
    }
    setLoading(false);
  };

  const filtered = search ? logs.filter((l) => l.toLowerCase().includes(search.toLowerCase())) : logs;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Log Viewer</h1>
        <p className="text-surface-400 text-sm mt-1">View Nginx access and error logs for your websites</p>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="label">Domain</label>
            {sitesLoading ? (
              <div className="input animate-pulse text-surface-500">Loading sites...</div>
            ) : (
              <select
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value)}
                className="input"
              >
                <option value="">Select domain...</option>
                {sites.map((s) => (
                  <option key={s.domain} value={s.domain}>{s.domain}</option>
                ))}
              </select>
            )}
          </div>
          <div>
            <label className="label">Log Type</label>
            <div className="flex rounded-lg overflow-hidden border border-surface-700">
              <button
                onClick={() => setLogType("access")}
                className={`flex-1 px-3 py-2 text-sm font-medium transition-all ${
                  logType === "access"
                    ? "bg-brand-600 text-white"
                    : "bg-surface-800 text-surface-400 hover:text-white"
                }`}
              >
                Access
              </button>
              <button
                onClick={() => setLogType("error")}
                className={`flex-1 px-3 py-2 text-sm font-medium transition-all ${
                  logType === "error"
                    ? "bg-brand-600 text-white"
                    : "bg-surface-800 text-surface-400 hover:text-white"
                }`}
              >
                Error
              </button>
            </div>
          </div>
          <div>
            <label className="label">Lines</label>
            <select value={lines} onChange={(e) => setLines(Number(e.target.value))} className="input">
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={200}>200</option>
              <option value={500}>500</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={fetchLogs}
              disabled={loading || !selectedDomain}
              className="btn-primary w-full"
            >
              <ScrollText size={14} /> View Logs
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
              type="text" value={search} onChange={(e) => setSearch(e.target.value)}
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
            <ScrollText size={48} className="mx-auto text-surface-700 mb-4" />
            <p className="text-surface-400 text-sm">Select a domain and click &quot;View Logs&quot; to see logs.</p>
          </div>
        ) : (
          <div className="bg-surface-950 rounded-lg border border-surface-800 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 bg-surface-900 border-b border-surface-800">
              <span className="text-xs text-surface-400">{selectedDomain} - {logType} log ({filtered.length} lines)</span>
              <button
                onClick={() => {
                  const b = new Blob([filtered.join("\n")], { type: "text/plain" });
                  const a = document.createElement("a");
                  a.href = URL.createObjectURL(b);
                  a.download = `${selectedDomain}-${logType}.log`;
                  a.click();
                }}
                className="btn-ghost text-xs"
              >
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
