"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { User, Shield, Mail, Calendar, Package, HardDrive, Globe, Database, RefreshCw, Eye, EyeOff } from "lucide-react";

export default function CustomerProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [quota, setQuota] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Password form
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showOld, setShowOld] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [pwLoading, setPwLoading] = useState(false);
  const [pwResult, setPwResult] = useState<{ success: boolean; msg: string } | null>(null);

  const fetchData = async () => {
    setLoading(true);
    const [meRes, quotaRes] = await Promise.all([api.getMe(), api.getQuota()]);
    if (meRes.success && meRes.data) setProfile(meRes.data);
    if (quotaRes.success && quotaRes.data) setQuota(quotaRes.data);
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setPwResult({ success: false, msg: "New password and confirmation do not match." });
      return;
    }
    if (newPassword.length < 6) {
      setPwResult({ success: false, msg: "Password must be at least 6 characters." });
      return;
    }
    setPwLoading(true);
    setPwResult(null);
    const res = await api.changePassword(oldPassword, newPassword);
    setPwResult({
      success: !!res.success,
      msg: res.success ? "Password changed successfully!" : (res.error || "Failed to change password"),
    });
    setPwLoading(false);
    if (res.success) {
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    }
  };

  const displayUser = profile || user;

  const quotaBars = [
    {
      label: "Disk Space",
      used: quota?.disk_used || "0",
      limit: quota?.disk_limit || "-",
      percent: quota?.disk_limit ? Math.min((parseFloat(quota.disk_used) / parseFloat(quota.disk_limit)) * 100, 100) : 0,
      color: "bg-cyan-500",
      icon: HardDrive,
    },
    {
      label: "Websites",
      used: quota?.sites_used ?? "?",
      limit: quota?.sites_limit ?? "?",
      percent: quota?.sites_limit ? Math.min((quota.sites_used / quota.sites_limit) * 100, 100) : 0,
      color: "bg-blue-500",
      icon: Globe,
    },
    {
      label: "Databases",
      used: quota?.databases_used ?? "?",
      limit: quota?.databases_limit ?? "?",
      percent: quota?.databases_limit ? Math.min((quota.databases_used / quota.databases_limit) * 100, 100) : 0,
      color: "bg-purple-500",
      icon: Database,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">My Profile</h1>
        <p className="text-surface-400 text-sm mt-1">View account details and manage settings</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Account Info */}
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-brand-600/20 rounded-full flex items-center justify-center">
              <User size={24} className="text-brand-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Account Information</h2>
              <p className="text-xs text-surface-500">Your account details</p>
            </div>
          </div>

          {loading ? (
            <div className="animate-pulse text-surface-500">Loading...</div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-surface-900 rounded-lg">
                <User size={16} className="text-surface-500 flex-shrink-0" />
                <div>
                  <p className="text-xs text-surface-500">Username</p>
                  <p className="text-sm text-white font-medium">{displayUser?.username || "-"}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-surface-900 rounded-lg">
                <Mail size={16} className="text-surface-500 flex-shrink-0" />
                <div>
                  <p className="text-xs text-surface-500">Email</p>
                  <p className="text-sm text-white font-medium">{displayUser?.email || "-"}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-surface-900 rounded-lg">
                <User size={16} className="text-surface-500 flex-shrink-0" />
                <div>
                  <p className="text-xs text-surface-500">Full Name</p>
                  <p className="text-sm text-white font-medium">{displayUser?.full_name || "-"}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-surface-900 rounded-lg">
                <Package size={16} className="text-surface-500 flex-shrink-0" />
                <div>
                  <p className="text-xs text-surface-500">Package</p>
                  <p className="text-sm text-white font-medium">{displayUser?.package?.name || "-"}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-surface-900 rounded-lg">
                <Shield size={16} className="text-surface-500 flex-shrink-0" />
                <div>
                  <p className="text-xs text-surface-500">Role</p>
                  <p className="text-sm text-white font-medium capitalize">{displayUser?.role || "-"}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 bg-surface-900 rounded-lg">
                <Calendar size={16} className="text-surface-500 flex-shrink-0" />
                <div>
                  <p className="text-xs text-surface-500">Created</p>
                  <p className="text-sm text-white font-medium">{displayUser?.created_at || "-"}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Quota + Change Password */}
        <div className="space-y-6">
          {/* Quota Usage */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white">Resource Usage</h3>
              <button onClick={fetchData} disabled={loading} className="btn-ghost text-xs">
                <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
              </button>
            </div>
            {quota ? (
              <div className="space-y-5">
                {quotaBars.map((q) => (
                  <div key={q.label}>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <div className="flex items-center gap-2">
                        <q.icon size={14} className="text-surface-400" />
                        <span className="text-surface-400">{q.label}</span>
                      </div>
                      <span className="text-white font-medium">{q.used} / {q.limit}</span>
                    </div>
                    <div className="w-full bg-surface-800 rounded-full h-2">
                      <div className={`${q.color} h-2 rounded-full transition-all`} style={{ width: `${q.percent}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-surface-500 text-sm">No quota information available.</p>
            )}
          </div>

          {/* Change Password */}
          <div className="card">
            <h3 className="text-sm font-semibold text-white mb-4">Change Password</h3>
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div>
                <label className="label">Current Password</label>
                <div className="relative">
                  <input
                    type={showOld ? "text" : "password"}
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    className="input w-full pr-10"
                    placeholder="Enter current password"
                    required
                  />
                  <button type="button" onClick={() => setShowOld(!showOld)} className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-white">
                    {showOld ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
              <div>
                <label className="label">New Password</label>
                <div className="relative">
                  <input
                    type={showNew ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="input w-full pr-10"
                    placeholder="Enter new password"
                    required
                    minLength={6}
                  />
                  <button type="button" onClick={() => setShowNew(!showNew)} className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-white">
                    {showNew ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
              <div>
                <label className="label">Confirm New Password</label>
                <div className="relative">
                  <input
                    type={showConfirm ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="input w-full pr-10"
                    placeholder="Confirm new password"
                    required
                    minLength={6}
                  />
                  <button type="button" onClick={() => setShowConfirm(!showConfirm)} className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-white">
                    {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {pwResult && (
                <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${pwResult.success ? "bg-brand-900/30 border border-brand-800/50 text-brand-400" : "bg-red-900/30 border border-red-800/50 text-red-400"}`}>
                  {pwResult.success ? "✓" : "✗"} {pwResult.msg}
                </div>
              )}

              <button type="submit" disabled={pwLoading || !oldPassword || !newPassword || !confirmPassword} className="btn-primary w-full">
                {pwLoading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : "Change Password"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
