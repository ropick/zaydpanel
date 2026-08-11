'use client';

import { useSession, signOut } from 'next-auth/react';
import { useState } from 'react';

export default function AdminProfilePage() {
  const { data: session } = useSession();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    name: (session?.user as any)?.name || '',
    email: (session?.user as any)?.email || '',
  });

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    setError('');

    try {
      const res = await fetch('/api/admin/profile', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (data.success) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      } else {
        setError(data.message || 'Gagal menyimpan');
      }
    } catch {
      setError('Terjadi kesalahan');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Profil Admin</h1>

      <div className="bg-card border border-border rounded-lg p-6 space-y-6">
        {/* Avatar */}
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-purple-500/20 flex items-center justify-center">
            <span className="text-2xl font-bold text-purple-400">
              {form.name.charAt(0).toUpperCase()}
            </span>
          </div>
          <div>
            <div className="text-lg font-semibold text-foreground">{form.name || 'Admin'}</div>
            <div className="text-sm text-muted-foreground">{form.email}</div>
            <div className="text-xs text-purple-400 mt-1">Role: Administrator</div>
          </div>
        </div>

        <hr className="border-border" />

        {/* Edit Form */}
        <form onSubmit={handleSave} className="space-y-4">
          {saved && (
            <div className="bg-green-500/20 text-green-400 p-3 rounded-lg text-sm">
              Profil berhasil diperbarui
            </div>
          )}
          {error && (
            <div className="bg-red-500/20 text-red-400 p-3 rounded-lg text-sm">{error}</div>
          )}
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">Nama</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-4 py-2 bg-muted border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-purple-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full px-4 py-2 bg-muted border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-purple-500"
              required
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
            >
              {saving ? 'Menyimpan...' : 'Simpan Perubahan'}
            </button>
          </div>
        </form>
      </div>

      {/* Danger Zone */}
      <div className="bg-card border border-red-500/30 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-red-400 mb-2">Zona Bahaya</h2>
        <p className="text-sm text-muted-foreground mb-4">Keluar dari akun admin.</p>
        <button
          onClick={() => signOut({ callbackUrl: '/login' })}
          className="px-4 py-2 bg-red-600/20 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-600/30 transition-colors"
        >
          Logout
        </button>
      </div>
    </div>
  );
}
