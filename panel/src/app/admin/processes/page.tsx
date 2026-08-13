"use client";
import { useState, useEffect } from "react";
import { api, type ProcessInfo } from "@/lib/api";
import { Terminal, RefreshCw, Cpu, MemoryStick, ArrowUp, ArrowDown } from "lucide-react";

export default function ProcessesPage() {
  const [processes, setProcesses] = useState<ProcessInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortField, setSortField] = useState<keyof ProcessInfo>("cpu");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const fetchProcesses = async () => {
    setLoading(true);
    const res = await api.processes();
    if (res.success) setProcesses(res.data || []);
    setLoading(false);
  };

  useEffect(() => { fetchProcesses(); const i = setInterval(fetchProcesses, 10000); return () => clearInterval(i); }, []);

  const handleSort = (field: keyof ProcessInfo) => {
    if (sortField === field) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortField(field); setSortDir("desc"); }
  };

  const sorted = [...processes].sort((a, b) => {
    const va = a[sortField], vb = b[sortField];
    if (typeof va === "number" && typeof vb === "number") return sortDir === "desc" ? vb - va : va - vb;
    return sortDir === "desc" ? String(vb).localeCompare(String(va)) : String(va).localeCompare(String(vb));
  });

  const SortIcon = ({ field }: { field: keyof ProcessInfo }) => (
    <span className="ml-1 text-[10px]">
      {sortField === field ? (sortDir === "desc" ? <ArrowDown size={10} /> : <ArrowUp size={10} />) : ""}
    </span>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Processes</h1>
          <p className="text-surface-400 text-sm mt-1">Monitor proses yang berjalan di server</p>
        </div>
        <button onClick={fetchProcesses} disabled={loading} className="btn-secondary">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <Terminal size={18} className="text-surface-400" />
            <span className="text-surface-400 text-sm">Total Processes</span>
          </div>
          <p className="text-2xl font-bold text-white">{processes.length}</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <Cpu size={18} className="text-orange-400" />
            <span className="text-surface-400 text-sm">Highest CPU</span>
          </div>
          <p className="text-2xl font-bold text-white">{processes[0]?.cpu || 0}%</p>
          <p className="text-xs text-surface-500 truncate">{processes[0]?.command || "-"}</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <MemoryStick size={18} className="text-purple-400" />
            <span className="text-surface-400 text-sm">Highest Memory</span>
          </div>
          <p className="text-2xl font-bold text-white">{sorted.sort((a, b) => b.mem - a.mem)[0]?.mem || 0}%</p>
          <p className="text-xs text-surface-500 truncate">{sorted[0]?.command || "-"}</p>
        </div>
      </div>

      {/* Process Table */}
      <div className="card overflow-x-auto">
        {loading ? (
          <div className="animate-pulse text-surface-500 py-4">Loading processes...</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-800">
                <th className="text-left p-3 text-surface-400 font-medium cursor-pointer hover:text-white" onClick={() => handleSort("pid")}>PID <SortIcon field="pid" /></th>
                <th className="text-left p-3 text-surface-400 font-medium cursor-pointer hover:text-white" onClick={() => handleSort("user")}>User <SortIcon field="user" /></th>
                <th className="text-left p-3 text-surface-400 font-medium cursor-pointer hover:text-white" onClick={() => handleSort("cpu")}>CPU% <SortIcon field="cpu" /></th>
                <th className="text-left p-3 text-surface-400 font-medium cursor-pointer hover:text-white" onClick={() => handleSort("mem")}>MEM% <SortIcon field="mem" /></th>
                <th className="text-left p-3 text-surface-400 font-medium">Command</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-800/50">
              {sorted.map((p) => (
                <tr key={p.pid} className="hover:bg-surface-800/50 transition-colors">
                  <td className="p-3 font-mono text-surface-400">{p.pid}</td>
                  <td className="p-3 text-surface-300">{p.user}</td>
                  <td className="p-3">
                    <span className={`font-mono ${p.cpu > 50 ? "text-red-400" : p.cpu > 20 ? "text-yellow-400" : "text-surface-300"}`}>
                      {p.cpu.toFixed(1)}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`font-mono ${p.mem > 50 ? "text-red-400" : p.mem > 20 ? "text-yellow-400" : "text-surface-300"}`}>
                      {p.mem.toFixed(1)}
                    </span>
                  </td>
                  <td className="p-3 text-surface-200 font-mono text-xs truncate max-w-xs">{p.command}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
