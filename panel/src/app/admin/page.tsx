"use client";
import { useEffect, useState } from "react";
import { api, type ServerInfo, type ProcessInfo } from "@/lib/api";
import {
  Globe, Cpu, MemoryStick, HardDrive, Activity, Clock, ArrowUp, ArrowDown,
  Server, RefreshCw, Terminal, Zap, Lock
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const [sites, setSites] = useState<{ domain: string; home: string; exists: boolean; ssl?: boolean; has_wp?: boolean; type?: string; php_fpm?: boolean; php_version?: string }[]>([]);
  const [serverInfo, setServerInfo] = useState<ServerInfo | null>(null);
  const [processes, setProcesses] = useState<ProcessInfo[]>([]);
  const [agentOnline, setAgentOnline] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [sitesRes, healthRes, serverRes, procRes] = await Promise.all([
        api.listSites(),
        api.health(),
        api.serverInfo(),
        api.processes(),
      ]);
      if (sitesRes.success) setSites(sitesRes.data || []);
      if (healthRes.success && healthRes.data) setAgentOnline(true);
      if (serverRes.success) setServerInfo(serverRes.data as ServerInfo);
      if (procRes.success) setProcesses((procRes.data || []).slice(0, 5));
    } catch (err) { console.error("Dashboard fetch error:", err); }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);

  const memPercent = serverInfo ? Math.round(parseInt(serverInfo.memory_used) / parseInt(serverInfo.memory_total) * 100) : 0;
  const diskPercent = serverInfo
    ? Math.round(parseInt(serverInfo.disk_used.replace("G", "")) / parseInt(serverInfo.disk_total.replace("G", "")) * 100)
    : 0;

  const stats = [
    {
      label: "Total Websites", value: sites.length, sub: `${sites.filter(s => s.exists).length} Active · ${sites.filter(s => s.type === 'proxy').length} Proxy`,
      icon: Globe, color: "blue"
    },
    {
      label: "CPU", value: serverInfo ? `${serverInfo.cpu_percent}%` : "-",
      sub: serverInfo ? `${serverInfo.cpu_cores} cores` : "-",
      icon: Cpu, color: "orange", percent: serverInfo?.cpu_percent || 0
    },
    {
      label: "RAM", value: serverInfo ? `${memPercent}%` : "-",
      sub: serverInfo ? `${serverInfo.memory_used} MB of ${serverInfo.memory_total} MB` : "-",
      icon: MemoryStick, color: "purple", percent: memPercent
    },
    {
      label: "Disk", value: serverInfo ? `${diskPercent}%` : "-",
      sub: serverInfo ? `${serverInfo.disk_used} of ${serverInfo.disk_total}` : "-",
      icon: HardDrive, color: "cyan", percent: diskPercent
    },
  ];

  const colorMap: Record<string, { bg: string; text: string; bar: string }> = {
    blue: { bg: "bg-blue-500/20", text: "text-blue-400", bar: "bg-blue-500" },
    orange: { bg: "bg-orange-500/20", text: "text-orange-400", bar: "bg-orange-500" },
    purple: { bg: "bg-purple-500/20", text: "text-purple-400", bar: "bg-purple-500" },
    cyan: { bg: "bg-cyan-500/20", text: "text-cyan-400", bar: "bg-cyan-500" },
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-surface-400 mt-1">Overview server dan website Anda</p>
      </div>

      {/* Agent Status */}
      <div className="card mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity size={20} className={agentOnline ? "text-brand-500" : "text-red-500"} />
          <div>
            <p className="text-sm font-medium text-white">Agent</p>
            <p className="text-xs text-surface-500">Auto-refresh 15s</p>
          </div>
        </div>
        <span className={`text-xs font-medium px-3 py-1 rounded-full ${agentOnline ? "bg-brand-500/20 text-brand-400 border border-brand-500/30" : "bg-red-500/20 text-red-400 border border-red-500/30"}`}>
          {agentOnline ? "Online" : "Offline"}
        </span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((s) => {
          const c = colorMap[s.color];
          return (
            <div key={s.label} className="card">
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-10 h-10 rounded-lg ${c.bg} flex items-center justify-center`}>
                  <s.icon size={20} className={c.text} />
                </div>
                <p className="text-surface-400 text-sm">{s.label}</p>
              </div>
              <p className="text-3xl font-bold text-white">{s.value}</p>
              <p className="text-surface-500 text-xs mt-1">{s.sub}</p>
              {s.percent !== undefined && (
                <div className="mt-3 w-full bg-surface-800 rounded-full h-1.5">
                  <div className={`${c.bar} h-1.5 rounded-full transition-all`} style={{ width: `${Math.min(s.percent, 100)}%` }} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Middle Row: Network + Load Average + Uptime */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Network I/O */}
        <div className="card">
          <div className="flex items-center gap-3 mb-3">
            <Zap size={18} className="text-yellow-400" />
            <h3 className="text-sm font-semibold text-white">Network I/O</h3>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-green-400">
                <ArrowDown size={14} /> RX
              </div>
              <span className="text-white font-medium">{serverInfo?.net_rx_total || "-"}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2 text-blue-400">
                <ArrowUp size={14} /> TX
              </div>
              <span className="text-white font-medium">{serverInfo?.net_tx_total || "-"}</span>
            </div>
          </div>
        </div>

        {/* CPU Load Average */}
        <div className="card">
          <div className="flex items-center gap-3 mb-3">
            <Cpu size={18} className="text-orange-400" />
            <h3 className="text-sm font-semibold text-white">Load Average</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-surface-500">1 min</span>
              <span className="text-white font-mono">{serverInfo?.cpu_load_1m?.toFixed(2) || "-"}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-surface-500">5 min</span>
              <span className="text-white font-mono">{serverInfo?.cpu_load_5m?.toFixed(2) || "-"}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-surface-500">15 min</span>
              <span className="text-white font-mono">{serverInfo?.cpu_load_15m?.toFixed(2) || "-"}</span>
            </div>
          </div>
        </div>

        {/* Server Info */}
        <div className="card">
          <div className="flex items-center gap-3 mb-3">
            <Server size={18} className="text-surface-400" />
            <h3 className="text-sm font-semibold text-white">Server</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-surface-500">Hostname</span>
              <span className="text-white font-mono text-xs">{serverInfo?.hostname || "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-surface-500">OS</span>
              <span className="text-white text-xs">{serverInfo?.os || "-"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-surface-500">Uptime</span>
              <span className="text-brand-400 font-medium">{serverInfo?.uptime || "-"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row: Top Processes + Sites List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Processes */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Terminal size={16} className="text-surface-400" />
              <h3 className="text-sm font-semibold text-white">Top Processes</h3>
            </div>
            <Link href="/admin/processes" className="text-xs text-brand-400 hover:text-brand-300">View all</Link>
          </div>
          {processes.length === 0 ? (
            <p className="text-surface-500 text-xs">No data</p>
          ) : (
            <div className="space-y-2">
              {processes.map((p) => (
                <div key={p.pid} className="flex items-center justify-between p-2 bg-surface-900 rounded-lg text-xs">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-surface-500 font-mono w-8">{p.pid}</span>
                    <span className="text-white truncate">{p.command.split("/").pop()}</span>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="text-orange-400 font-mono">{p.cpu}%</span>
                    <span className="text-purple-400 font-mono">{p.mem}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sites List */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Websites</h3>
            <div className="flex gap-2">
              <button onClick={fetchData} disabled={loading} className="btn-ghost text-xs">
                <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Refresh
              </button>
              <Link href="/admin/sites" className="btn-primary text-xs">Manage</Link>
            </div>
          </div>
          {loading ? (
            <div className="animate-pulse text-surface-500 text-sm">Loading...</div>
          ) : sites.length === 0 ? (
            <p className="text-surface-500 text-sm">Belum ada website.</p>
          ) : (
            <div className="space-y-2">
              {sites.map((site) => (
                <div key={site.domain} className="flex items-center justify-between p-3 bg-surface-900 rounded-lg">
                  <div className="flex items-center gap-3 min-w-0">
                    <Globe size={16} className="text-brand-500 flex-shrink-0" />
                    <div className="min-w-0">
                      <span className="text-sm text-white font-medium">{site.domain}</span>
                      {site.ssl && <Lock size={12} className="inline text-green-400 ml-2" />}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {site.type === 'proxy' && (
                      <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400">Proxy</span>
                    )}
                    {site.has_wp && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-medium">WordPress</span>
                    )}
                    {site.exists ? (
                      <span className="text-xs px-2 py-0.5 rounded bg-brand-500/20 text-brand-400">Active</span>
                    ) : (
                      <span className="text-xs px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400">No Home</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Version */}
      <div className="mt-8 text-center text-surface-600 text-xs">
        <span className="px-2 py-1 bg-surface-900 rounded">v2.1</span>
        <span className="ml-2">ZaydPanel &mdash; Shared Hosting Control Panel</span>
      </div>
    </div>
  );
}
