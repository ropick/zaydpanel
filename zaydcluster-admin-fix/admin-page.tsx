'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface Stats {
  totalOrders: number;
  activeOrders: number;
  pendingOrders: number;
  totalRevenue: number;
  pendingRevenue: number;
  totalCustomers: number;
  activeSubscriptions: number;
  recentOrders: any[];
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/admin/stats')
      .then((r) => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then((d) => {
        if (d.success) setStats(d.stats);
        else throw new Error(d.message || 'Gagal memuat');
      })
      .catch((err) => {
        console.error('Stats fetch error:', err);
        setError('Gagal memuat data: ' + err.message);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-muted-foreground text-lg">Memuat data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="text-red-400 text-lg">{error}</div>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
        >
          Coba Lagi
        </button>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <div className="text-muted-foreground">Data tidak tersedia</div>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
        >
          Muat Ulang
        </button>
      </div>
    );
  }

  const cards = [
    { label: 'Total Pesanan', value: stats.totalOrders, color: 'border-l-blue-500' },
    { label: 'Pesanan Aktif', value: stats.activeOrders, color: 'border-l-green-500' },
    { label: 'Pesanan Pending', value: stats.pendingOrders, color: 'border-l-yellow-500' },
    { label: 'Total Pendapatan', value: `Rp ${stats.totalRevenue.toLocaleString('id-ID')}`, color: 'border-l-purple-500' },
    { label: 'Pending Pembayaran', value: `Rp ${stats.pendingRevenue.toLocaleString('id-ID')}`, color: 'border-l-orange-500' },
    { label: 'Total Pelanggan', value: stats.totalCustomers, color: 'border-l-indigo-500' },
    { label: 'Langganan Aktif', value: stats.activeSubscriptions, color: 'border-l-teal-500' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Admin Dashboard</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => (
          <div
            key={card.label}
            className={`bg-card border border-border border-l-4 ${card.color} p-5 rounded-lg shadow-sm`}
          >
            <div className="text-sm text-muted-foreground">{card.label}</div>
            <div className="text-2xl font-bold text-foreground mt-1">{card.value}</div>
          </div>
        ))}
      </div>

      {/* Recent Orders Table */}
      <div className="bg-card border border-border rounded-lg shadow-sm">
        <div className="flex justify-between items-center p-5 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">Pesanan Terbaru</h2>
          <Link href="/admin/orders" className="text-purple-400 text-sm hover:underline">
            Lihat Semua
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">No. Pesanan</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Pelanggan</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Paket</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Total</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Status</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Tanggal</th>
              </tr>
            </thead>
            <tbody>
              {stats.recentOrders.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-muted-foreground">
                    Belum ada pesanan
                  </td>
                </tr>
              ) : (
                stats.recentOrders.map((order: any) => (
                  <tr key={order.id} className="border-b border-border hover:bg-muted/30">
                    <td className="py-3 px-4 font-medium text-foreground">{order.orderNumber}</td>
                    <td className="py-3 px-4 text-foreground">{order.name || order.user?.name}</td>
                    <td className="py-3 px-4 text-muted-foreground">{order.package}</td>
                    <td className="py-3 px-4 text-foreground">Rp {order.totalAmount.toLocaleString('id-ID')}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          order.status === 'active'
                            ? 'bg-green-500/20 text-green-400'
                            : order.status === 'pending'
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : order.status === 'confirmed'
                            ? 'bg-blue-500/20 text-blue-400'
                            : order.status === 'suspended'
                            ? 'bg-red-500/20 text-red-400'
                            : 'bg-muted text-muted-foreground'
                        }`}
                      >
                        {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground">
                      {new Date(order.createdAt).toLocaleDateString('id-ID')}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
