"use client";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import {
  Package as PackageIcon,
  RefreshCw,
  Plus,
  Pencil,
  Trash2,
  X,
  Loader2,
  HardDrive,
  ArrowUpDown,
  Globe,
  Database,
  FolderOpen,
  Mail,
  DollarSign,
} from "lucide-react";

interface PackageInfo {
  id: number;
  name: string;
  slug: string;
  disk_quota?: string;
  bandwidth?: string;
  max_sites?: number;
  max_databases?: number;
  max_ftp?: number;
  max_email?: number;
  price_monthly?: number;
  description?: string;
}

const emptyForm = {
  name: "",
  slug: "",
  disk_quota: "",
  bandwidth: "",
  max_sites: "",
  max_databases: "",
  max_ftp: "",
  max_email: "",
  price_monthly: "",
  description: "",
};

type ToastState = {
  success: boolean;
  msg: string;
} | null;

function formatRupiah(amount?: number | null): string {
  if (amount == null || amount === 0) return "Free";
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

function StatItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number | undefined;
}) {
  const display = value !== undefined && value !== null && value !== "" ? String(value) : "Unlimited";
  return (
    <div className="flex items-center gap-2 text-sm">
      <Icon size={14} className="text-surface-500 flex-shrink-0" />
      <span className="text-surface-400">{label}:</span>
      <span className="text-surface-200 font-medium">{display}</span>
    </div>
  );
}

export default function PackagesPage() {
  const [packages, setPackages] = useState<PackageInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<ToastState>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({ ...emptyForm });

  const fetchPackages = useCallback(async () => {
    setLoading(true);
    const res = await api.listPackages();
    if (res.success) setPackages(res.data || []);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchPackages();
  }, [fetchPackages]);

  const showToast = (success: boolean, msg: string) => {
    setToast({ success, msg });
    setTimeout(() => setToast(null), 4000);
  };

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  };

  const openAddForm = () => {
    setEditingId(null);
    setForm({ ...emptyForm });
    setShowForm(true);
  };

  const openEditForm = (pkg: PackageInfo) => {
    setEditingId(pkg.id);
    setForm({
      name: pkg.name || "",
      slug: pkg.slug || "",
      disk_quota: pkg.disk_quota || "",
      bandwidth: pkg.bandwidth || "",
      max_sites: pkg.max_sites != null ? String(pkg.max_sites) : "",
      max_databases: pkg.max_databases != null ? String(pkg.max_databases) : "",
      max_ftp: pkg.max_ftp != null ? String(pkg.max_ftp) : "",
      max_email: pkg.max_email != null ? String(pkg.max_email) : "",
      price_monthly: pkg.price_monthly != null ? String(pkg.price_monthly) : "",
      description: pkg.description || "",
    });
    setShowForm(true);
  };

  const closeForm = () => {
    setShowForm(false);
    setEditingId(null);
    setForm({ ...emptyForm });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSubmitting(true);

    const payload: Record<string, any> = {
      name: form.name.trim(),
      slug: form.slug.trim() || generateSlug(form.name.trim()),
      disk_quota: form.disk_quota.trim() || undefined,
      bandwidth: form.bandwidth.trim() || undefined,
      max_sites: form.max_sites ? Number(form.max_sites) : undefined,
      max_databases: form.max_databases ? Number(form.max_databases) : undefined,
      max_ftp: form.max_ftp ? Number(form.max_ftp) : undefined,
      max_email: form.max_email ? Number(form.max_email) : undefined,
      price_monthly: form.price_monthly ? Number(form.price_monthly) : undefined,
      description: form.description.trim() || undefined,
    };

    let res;
    if (editingId !== null) {
      res = await api.updatePackage({ id: editingId, ...payload });
    } else {
      res = await api.createPackage(payload);
    }

    if (res.success) {
      showToast(true, editingId ? "Package updated successfully" : "Package created successfully");
      closeForm();
      fetchPackages();
    } else {
      showToast(false, res.error || "Operation failed");
    }
    setSubmitting(false);
  };

  const handleDelete = async (pkg: PackageInfo) => {
    if (!confirm(`Delete package "${pkg.name}"?\nUsers with this package will lose their assignment.`)) return;
    const res = await api.deletePackage(pkg.id);
    if (res.success) {
      showToast(true, `Package "${pkg.name}" deleted`);
      fetchPackages();
    } else {
      showToast(false, res.error || "Failed to delete package");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Packages</h1>
          <p className="text-surface-400 text-sm mt-1">Manage hosting packages and quotas</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchPackages} disabled={loading} className="btn-secondary">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button onClick={openAddForm} className="btn-primary">
            <Plus size={14} /> Add Package
          </button>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div
          className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${
            toast.success
              ? "bg-brand-900/30 border border-brand-800/50 text-brand-400"
              : "bg-red-900/30 border border-red-800/50 text-red-400"
          }`}
        >
          {toast.success ? "✓" : "✗"} {toast.msg}
          <button onClick={() => setToast(null)} className="ml-auto opacity-60 hover:opacity-100">
            ✕
          </button>
        </div>
      )}

      {/* Add/Edit Form */}
      {showForm && (
        <div className="card border-brand-700/50">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">
              {editingId !== null ? "Edit Package" : "Add New Package"}
            </h2>
            <button onClick={closeForm} className="btn-ghost p-2 text-surface-400 hover:text-white">
              <X size={16} />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Package Name *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. Starter"
                  value={form.name}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      name: e.target.value,
                      slug: editingId === null ? generateSlug(e.target.value) : form.slug,
                    })
                  }
                  required
                  disabled={submitting}
                />
              </div>
              <div>
                <label className="label">Slug</label>
                <input
                  type="text"
                  className="input font-mono"
                  placeholder="e.g. starter"
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                  disabled={submitting}
                />
              </div>
              <div>
                <label className="label">Disk Quota</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. 10G, 50G, 100G"
                  value={form.disk_quota}
                  onChange={(e) => setForm({ ...form, disk_quota: e.target.value })}
                  disabled={submitting}
                />
              </div>
              <div>
                <label className="label">Bandwidth</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. 100G, 500G, Unlimited"
                  value={form.bandwidth}
                  onChange={(e) => setForm({ ...form, bandwidth: e.target.value })}
                  disabled={submitting}
                />
              </div>
              <div>
                <label className="label">Max Sites</label>
                <input
                  type="number"
                  className="input"
                  placeholder="e.g. 5"
                  min="0"
                  value={form.max_sites}
                  onChange={(e) => setForm({ ...form, max_sites: e.target.value })}
                  disabled={submitting}
                />
              </div>
              <div>
                <label className="label">Max Databases</label>
                <input
                  type="number"
                  className="input"
                  placeholder="e.g. 10"
                  min="0"
                  value={form.max_databases}
                  onChange={(e) => setForm({ ...form, max_databases: e.target.value })}
                  disabled={submitting}
                />
              </div>
              <div>
                <label className="label">Max FTP Accounts</label>
                <input
                  type="number"
                  className="input"
                  placeholder="e.g. 5"
                  min="0"
                  value={form.max_ftp}
                  onChange={(e) => setForm({ ...form, max_ftp: e.target.value })}
                  disabled={submitting}
                />
              </div>
              <div>
                <label className="label">Max Email Accounts</label>
                <input
                  type="number"
                  className="input"
                  placeholder="e.g. 10"
                  min="0"
                  value={form.max_email}
                  onChange={(e) => setForm({ ...form, max_email: e.target.value })}
                  disabled={submitting}
                />
              </div>
              <div>
                <label className="label">Price Monthly (IDR)</label>
                <input
                  type="number"
                  className="input"
                  placeholder="e.g. 50000"
                  min="0"
                  value={form.price_monthly}
                  onChange={(e) => setForm({ ...form, price_monthly: e.target.value })}
                  disabled={submitting}
                />
              </div>
            </div>
            <div>
              <label className="label">Description</label>
              <textarea
                className="input min-h-[80px] resize-y"
                placeholder="Brief description of this package..."
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                disabled={submitting}
                rows={3}
              />
            </div>
            <div className="flex gap-2 pt-2">
              <button type="submit" disabled={submitting} className="btn-primary">
                {submitting && <Loader2 size={14} className="animate-spin" />}
                {editingId !== null ? "Update Package" : "Create Package"}
              </button>
              <button type="button" onClick={closeForm} disabled={submitting} className="btn-secondary">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Package Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse h-64" />
          ))}
        </div>
      ) : packages.length === 0 ? (
        <div className="card text-center py-12">
          <PackageIcon size={48} className="mx-auto text-surface-700 mb-4" />
          <h3 className="text-lg font-medium text-surface-300 mb-2">No packages yet</h3>
          <p className="text-surface-500 text-sm mb-4">Create the first hosting package to get started</p>
          <button onClick={openAddForm} className="btn-primary">
            <Plus size={14} /> Add Package
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {packages.map((pkg) => (
            <div key={pkg.id} className="card flex flex-col">
              {/* Card Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="min-w-0">
                  <h3 className="text-lg font-semibold text-white truncate">{pkg.name}</h3>
                  <p className="text-surface-500 text-xs font-mono mt-0.5">{pkg.slug}</p>
                </div>
                <span className="text-lg font-bold text-brand-400 flex-shrink-0 ml-3">
                  {formatRupiah(pkg.price_monthly)}
                  {pkg.price_monthly && pkg.price_monthly > 0 && (
                    <span className="text-xs text-surface-500 font-normal">/mo</span>
                  )}
                </span>
              </div>

              {/* Description */}
              {pkg.description && (
                <p className="text-surface-400 text-sm mb-4 line-clamp-2">{pkg.description}</p>
              )}

              {/* Quota Stats */}
              <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 mb-4 flex-1">
                <StatItem icon={HardDrive} label="Disk" value={pkg.disk_quota} />
                <StatItem icon={ArrowUpDown} label="Bandwidth" value={pkg.bandwidth} />
                <StatItem icon={Globe} label="Sites" value={pkg.max_sites} />
                <StatItem icon={Database} label="Databases" value={pkg.max_databases} />
                <StatItem icon={FolderOpen} label="FTP" value={pkg.max_ftp} />
                <StatItem icon={Mail} label="Email" value={pkg.max_email} />
              </div>

              {/* Card Actions */}
              <div className="flex items-center gap-2 pt-4 border-t border-surface-700">
                <button
                  onClick={() => openEditForm(pkg)}
                  className="btn-ghost text-xs flex-1"
                >
                  <Pencil size={12} /> Edit
                </button>
                <button
                  onClick={() => handleDelete(pkg)}
                  className="btn-ghost text-xs flex-1 text-red-400 hover:text-red-300 hover:bg-red-900/20"
                >
                  <Trash2 size={12} /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
