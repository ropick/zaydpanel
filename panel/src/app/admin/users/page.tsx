"use client";
import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import {
  Users as UsersIcon,
  RefreshCw,
  Plus,
  Pencil,
  Ban,
  Trash2,
  UserCheck,
  UserX,
  X,
  Loader2,
} from "lucide-react";

interface UserInfo {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: string;
  package_id?: number;
  package_name?: string;
  status: string;
  created_at?: string;
}

interface PackageInfo {
  id: number;
  name: string;
  slug: string;
}

const emptyForm = {
  username: "",
  email: "",
  full_name: "",
  role: "user",
  package_id: "" as string,
  status: "active",
};

type ToastState = {
  success: boolean;
  msg: string;
} | null;

export default function UsersPage() {
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [packages, setPackages] = useState<PackageInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<ToastState>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({ ...emptyForm });

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    const res = await api.listUsers();
    if (res.success) setUsers(res.data || []);
    setLoading(false);
  }, []);

  const fetchPackages = useCallback(async () => {
    const res = await api.listPackages();
    if (res.success) setPackages(res.data || []);
  }, []);

  useEffect(() => {
    fetchUsers();
    fetchPackages();
  }, [fetchUsers, fetchPackages]);

  const showToast = (success: boolean, msg: string) => {
    setToast({ success, msg });
    setTimeout(() => setToast(null), 4000);
  };

  const openAddForm = () => {
    setEditingId(null);
    setForm({ ...emptyForm });
    setShowForm(true);
  };

  const openEditForm = (user: UserInfo) => {
    setEditingId(user.id);
    setForm({
      username: user.username,
      email: user.email || "",
      full_name: user.full_name || "",
      role: user.role || "user",
      package_id: user.package_id ? String(user.package_id) : "",
      status: user.status || "active",
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
    if (!form.username.trim()) return;
    setSubmitting(true);

    const payload = {
      username: form.username.trim(),
      email: form.email.trim() || undefined,
      full_name: form.full_name.trim() || undefined,
      role: form.role,
      package_id: form.package_id ? Number(form.package_id) : undefined,
      status: form.status,
    };

    let res;
    if (editingId !== null) {
      res = await api.updateUser({ id: editingId, ...payload });
    } else {
      res = await api.createUser(payload);
    }

    if (res.success) {
      showToast(true, editingId ? "User updated successfully" : "User created successfully");
      closeForm();
      fetchUsers();
    } else {
      showToast(false, res.error || "Operation failed");
    }
    setSubmitting(false);
  };

  const handleDelete = async (user: UserInfo) => {
    if (!confirm(`Delete user "${user.username}"?\nThis action cannot be undone.`)) return;
    const res = await api.deleteUser(user.id);
    if (res.success) {
      showToast(true, `User "${user.username}" deleted`);
      fetchUsers();
    } else {
      showToast(false, res.error || "Failed to delete user");
    }
  };

  const handleSuspend = async (user: UserInfo) => {
    const newStatus = user.status === "suspended" ? "active" : "suspended";
    const res = await api.updateUser({ id: user.id, status: newStatus });
    if (res.success) {
      showToast(true, `User "${user.username}" ${newStatus === "suspended" ? "suspended" : "activated"}`);
      fetchUsers();
    } else {
      showToast(false, res.error || "Failed to update user status");
    }
  };

  const totalUsers = users.length;
  const activeUsers = users.filter((u) => u.status === "active").length;
  const suspendedUsers = users.filter((u) => u.status === "suspended").length;
  const adminUsers = users.filter((u) => u.role === "admin").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Users</h1>
          <p className="text-surface-400 text-sm mt-1">Manage all users on the server</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchUsers} disabled={loading} className="btn-secondary">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
          <button onClick={openAddForm} className="btn-primary">
            <Plus size={14} /> Add User
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-surface-400 text-sm">Total Users</p>
          <p className="text-2xl font-bold text-white">{totalUsers}</p>
        </div>
        <div className="card">
          <p className="text-surface-400 text-sm">Active</p>
          <p className="text-2xl font-bold text-brand-400">{activeUsers}</p>
        </div>
        <div className="card">
          <p className="text-surface-400 text-sm">Suspended</p>
          <p className="text-2xl font-bold text-yellow-400">{suspendedUsers}</p>
        </div>
        <div className="card">
          <p className="text-surface-400 text-sm">Admins</p>
          <p className="text-2xl font-bold text-blue-400">{adminUsers}</p>
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
              {editingId !== null ? "Edit User" : "Add New User"}
            </h2>
            <button onClick={closeForm} className="btn-ghost p-2 text-surface-400 hover:text-white">
              <X size={16} />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Username *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. johndoe"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  required
                  disabled={submitting}
                />
              </div>
              <div>
                <label className="label">Email</label>
                <input
                  type="email"
                  className="input"
                  placeholder="e.g. john@example.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  disabled={submitting}
                />
              </div>
              <div>
                <label className="label">Full Name</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. John Doe"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  disabled={submitting}
                />
              </div>
              <div>
                <label className="label">Role</label>
                <select
                  className="input"
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                  disabled={submitting}
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                  <option value="reseller">Reseller</option>
                </select>
              </div>
              <div>
                <label className="label">Package</label>
                <select
                  className="input"
                  value={form.package_id}
                  onChange={(e) => setForm({ ...form, package_id: e.target.value })}
                  disabled={submitting}
                >
                  <option value="">None</option>
                  {packages.map((pkg) => (
                    <option key={pkg.id} value={String(pkg.id)}>
                      {pkg.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Status</label>
                <select
                  className="input"
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  disabled={submitting}
                >
                  <option value="active">Active</option>
                  <option value="suspended">Suspended</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <button type="submit" disabled={submitting} className="btn-primary">
                {submitting && <Loader2 size={14} className="animate-spin" />}
                {editingId !== null ? "Update User" : "Create User"}
              </button>
              <button type="button" onClick={closeForm} disabled={submitting} className="btn-secondary">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Users Table */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card animate-pulse h-16" />
          ))}
        </div>
      ) : users.length === 0 ? (
        <div className="card text-center py-12">
          <UsersIcon size={48} className="mx-auto text-surface-700 mb-4" />
          <h3 className="text-lg font-medium text-surface-300 mb-2">No users yet</h3>
          <p className="text-surface-500 text-sm mb-4">Create the first user to get started</p>
          <button onClick={openAddForm} className="btn-primary">
            <Plus size={14} /> Add User
          </button>
        </div>
      ) : (
        <div className="card !p-0 overflow-hidden">
          {/* Desktop table */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-700">
                  <th className="text-left text-surface-400 font-medium px-6 py-3">Username</th>
                  <th className="text-left text-surface-400 font-medium px-6 py-3">Email</th>
                  <th className="text-left text-surface-400 font-medium px-6 py-3">Role</th>
                  <th className="text-left text-surface-400 font-medium px-6 py-3">Package</th>
                  <th className="text-left text-surface-400 font-medium px-6 py-3">Status</th>
                  <th className="text-left text-surface-400 font-medium px-6 py-3">Created</th>
                  <th className="text-right text-surface-400 font-medium px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="max-h-96 overflow-y-auto">
                {users.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-surface-700/50 hover:bg-surface-700/30 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-surface-700 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-xs font-semibold text-surface-300">
                            {user.username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className="text-white font-medium">{user.username}</p>
                          {user.full_name && (
                            <p className="text-surface-500 text-xs">{user.full_name}</p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-surface-300">{user.email || "—"}</td>
                    <td className="px-6 py-4">
                      <span
                        className={
                          user.role === "admin"
                            ? "badge-blue"
                            : user.role === "reseller"
                            ? "badge-yellow"
                            : "badge-green"
                        }
                      >
                        {user.role || "user"}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-surface-300">{user.package_name || "—"}</td>
                    <td className="px-6 py-4">
                      <span className={user.status === "active" ? "badge-green" : "badge-yellow"}>
                        {user.status === "active" ? "Active" : "Suspended"}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-surface-400">
                      {user.created_at
                        ? new Date(user.created_at).toLocaleDateString("id-ID", {
                            day: "numeric",
                            month: "short",
                            year: "numeric",
                          })
                        : "—"}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => openEditForm(user)}
                          className="btn-ghost text-xs px-2.5 py-1.5"
                          title="Edit user"
                        >
                          <Pencil size={12} /> Edit
                        </button>
                        <button
                          onClick={() => handleSuspend(user)}
                          className={`btn-ghost text-xs px-2.5 py-1.5 ${
                            user.status === "suspended"
                              ? "text-brand-400 hover:bg-brand-900/20"
                              : "text-yellow-400 hover:bg-yellow-900/20"
                          }`}
                          title={user.status === "suspended" ? "Activate user" : "Suspend user"}
                        >
                          {user.status === "suspended" ? (
                            <UserCheck size={12} />
                          ) : (
                            <Ban size={12} />
                          )}
                          {user.status === "suspended" ? "Activate" : "Suspend"}
                        </button>
                        <button
                          onClick={() => handleDelete(user)}
                          className="btn-ghost text-xs px-2.5 py-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/20"
                          title="Delete user"
                        >
                          <Trash2 size={12} /> Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden divide-y divide-surface-700/50 max-h-[480px] overflow-y-auto">
            {users.map((user) => (
              <div key={user.id} className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-surface-700 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-sm font-semibold text-surface-300">
                        {user.username.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-white font-medium">{user.username}</p>
                      {user.full_name && (
                        <p className="text-surface-500 text-xs">{user.full_name}</p>
                      )}
                    </div>
                  </div>
                  <span className={user.status === "active" ? "badge-green" : "badge-yellow"}>
                    {user.status === "active" ? "Active" : "Suspended"}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="text-surface-400">{user.email || "No email"}</span>
                  <span className="text-surface-600">·</span>
                  <span
                    className={
                      user.role === "admin"
                        ? "badge-blue"
                        : user.role === "reseller"
                        ? "badge-yellow"
                        : "badge-green"
                    }
                  >
                    {user.role || "user"}
                  </span>
                  {user.package_name && (
                    <>
                      <span className="text-surface-600">·</span>
                      <span className="text-surface-400">{user.package_name}</span>
                    </>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openEditForm(user)}
                    className="btn-ghost text-xs px-3 py-1.5"
                  >
                    <Pencil size={12} /> Edit
                  </button>
                  <button
                    onClick={() => handleSuspend(user)}
                    className={`btn-ghost text-xs px-3 py-1.5 ${
                      user.status === "suspended"
                        ? "text-brand-400 hover:bg-brand-900/20"
                        : "text-yellow-400 hover:bg-yellow-900/20"
                    }`}
                  >
                    {user.status === "suspended" ? (
                      <UserCheck size={12} />
                    ) : (
                      <Ban size={12} />
                    )}
                    {user.status === "suspended" ? "Activate" : "Suspend"}
                  </button>
                  <button
                    onClick={() => handleDelete(user)}
                    className="btn-ghost text-xs px-3 py-1.5 text-red-400 hover:text-red-300 hover:bg-red-900/20"
                  >
                    <Trash2 size={12} /> Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
