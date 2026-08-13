"use client";
import { useState, useEffect } from "react";
import { api, type ServerInfo } from "@/lib/api";
import { Activity, Cpu, HardDrive, MemoryStick, RefreshCw, Clock, Server as ServerIcon, Zap, ArrowUp, ArrowDown, Info } from "lucide-react";

export default function ServerInfoPage() {
  const [info, setInfo] = useState<ServerInfo | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchInfo = async () => {
    const res = await api.serverInfo();
    if (res.success) setInfo(res.data as ServerInfo);
    setLoading(false);
  };

  useEffect(() => { fetchInfo(); const i = setInterval(fetchInfo, 10000); return () => clearInterval(i); }, []);

  const memPct = info ? Math.round(parseInt(info.memory_used) / parseInt(info.memory_total) * 100) : 0;
  const diskPct = info ? Math.round(parseInt(info.disk_used.replace("G", "")) / parseInt(info.disk_total.replace("G", "")) * 100) : 0;

  const items = [
    {
      icon: <Clock size={24} className="text-brand-400" />, iconBg: "bg-brand-500/20",
      label: "Uptime", value: info?.uptime || "-", sub: "Server running time"
    },
    {
      icon: <Cpu size={24} className="text-orange-400" />, iconBg: "bg-orange-500/20",
      label: "CPU Usage", value: `${info?.cpu_percent || 0}%`,
      sub: `${info?.cpu_cores || "-"} cores`, percent: info?.cpu_percent || 0, barColor: "bg-orange-500"
    },
    {
      icon: <MemoryStick size={24} className="text-purple-400" />, iconBg: "bg-purple-500/20",
      label: "RAM", value: `${info?.memory_used || 0} MB / ${info?.memory_total || 0} MB`,
      sub: `${memPct}% used`, percent: memPct, barColor: "bg-purple-500"
    },
    {
      icon: <HardDrive size={24} className="text-cyan-400" />, iconBg: "bg-cyan-500/20",
      label: "Disk", value: `${info?.disk_used || "-"} / ${info?.disk_total || "-"}`,
      sub: `${diskPct}% used`, percent: diskPct, barColor: "bg-cyan-500"
    },
    {
      icon: <Zap size={24} className="text-yellow-400" />, iconBg: "bg-yellow-500/20",
      label: "Load Average",
      value: info ? `${info.cpu_load_1m?.toFixed(2) || "-"} / ${info.cpu_load_5m?.toFixed(2) || "-"} / ${info.cpu_load_15m?.toFixed(2) || "-"}` : "-",
      sub: "1m / 5m / 15m"
    },
    {
      icon: <Zap size={24} className="text-green-400" />, iconBg: "bg-green-500/20",
      label: "Network",
      value: info ? `RX: ${info.net_rx_total || "-"} / TX: ${info.net_tx_total || "-"}` : "-",
      sub: "Total traffic"
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Server Info</h1>
          <p className="text-surface-400 text-sm mt-1">Informasi lengkap server</p>
        </div>
        <button onClick={fetchInfo} disabled={loading} className="btn-secondary">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>

      {loading ? (
        <div className="animate-pulse text-surface-500">Loading...</div>
      ) : info && (
        <>
          {/* Server Overview */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <ServerIcon size={20} className="text-surface-400" />
              <h3 className="text-sm font-semibold text-white">System Information</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-3 bg-surface-900 rounded-lg">
                <p className="text-xs text-surface-500 mb-1">Hostname</p>
                <p className="text-white font-mono text-sm">{info.hostname || "-"}</p>
              </div>
              <div className="p-3 bg-surface-900 rounded-lg">
                <p className="text-xs text-surface-500 mb-1">Operating System</p>
                <p className="text-white text-sm">{info.os || "-"}</p>
              </div>
              <div className="p-3 bg-surface-900 rounded-lg">
                <p className="text-xs text-surface-500 mb-1">Kernel</p>
                <p className="text-white font-mono text-sm">{info.kernel || "-"}</p>
              </div>
              <div className="p-3 bg-surface-900 rounded-lg">
                <p className="text-xs text-surface-500 mb-1">Server Time</p>
                <p className="text-white text-sm">{info.server_time || "-"}</p>
              </div>
            </div>
          </div>

          {/* Resource Cards */}
          <div className="grid gap-4">
            {items.map((item) => (
              <div key={item.label} className="card flex items-center gap-4">
                <div className={`w-12 h-12 rounded-lg ${item.iconBg} flex items-center justify-center flex-shrink-0`}>
                  {item.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-surface-400 text-sm">{item.label}</p>
                  <p className="text-xl font-bold text-white truncate">{item.value}</p>
                  <p className="text-xs text-surface-500">{item.sub}</p>
                </div>
                {item.percent !== undefined && (
                  <div className="w-32 bg-surface-800 rounded-full h-3 flex-shrink-0 hidden sm:block">
                    <div className={`${item.barColor} h-3 rounded-full transition-all`} style={{ width: `${Math.min(item.percent, 100)}%` }} />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Services */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <Activity size={18} className="text-surface-400" />
              <h3 className="text-sm font-semibold text-white">Quick Service Restart</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {["nginx", "mysql", "php-fpm", "named"].map((svc) => (
                <ServiceRestartButton key={svc} service={svc} />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function ServiceRestartButton({ service }: { service: string }) {
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleRestart = async () => {
    if (!confirm(`Restart service ${service}?`)) return;
    setLoading(true);
    const res = await api.restartService(service);
    if (res.success) { setDone(true); setTimeout(() => setDone(false), 3000); }
    setLoading(false);
  };

  return (
    <button onClick={handleRestart} disabled={loading} className="p-3 bg-surface-900 rounded-lg text-left hover:bg-surface-800 transition-colors">
      <p className={`text-sm font-medium ${done ? "text-brand-400" : "text-white"}`}>{service}</p>
      <p className="text-xs text-surface-500 mt-1">
        {loading ? "Restarting..." : done ? "Restarted!" : "Click to restart"}
      </p>
    </button>
  );
}
