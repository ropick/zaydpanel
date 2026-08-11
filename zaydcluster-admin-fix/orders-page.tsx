'use client';

import { useEffect, useState } from 'react';

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  const fetchOrders = (status?: string) => {
    setLoading(true);
    const url = status ? `/api/admin/orders?status=${status}` : '/api/admin/orders';
    fetch(url)
      .then((r) => r.json())
      .then((d) => {
        if (d.success) setOrders(d.orders);
      })
      .catch((err) => console.error('Orders fetch error:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchOrders(filter || undefined);
  }, [filter]);

  const updateStatus = async (orderId: string, status: string) => {
    try {
      const res = await fetch('/api/admin/orders', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ orderId, status }),
      });
      const data = await res.json();
      if (data.success) fetchOrders(filter || undefined);
    } catch (err) {
      console.error('Update status error:', err);
    }
  };

  if (loading) {
    return <div className="text-center py-20 text-muted-foreground">Memuat...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-foreground">Pesanan</h1>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="bg-muted border border-border rounded-lg px-3 py-2 text-sm text-foreground"
        >
          <option value="">Semua</option>
          <option value="pending">Pending</option>
          <option value="confirmed">Confirmed</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="cancelled">Cancelled</option>
          <option value="expired">Expired</option>
        </select>
      </div>

      <div className="bg-card border border-border rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">No. Pesanan</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Pelanggan</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Paket</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Siklus</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Domain</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Total</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Status</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {orders.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-muted-foreground">
                    Belum ada pesanan
                  </td>
                </tr>
              ) : (
                orders.map((order) => (
                  <tr key={order.id} className="border-b border-border hover:bg-muted/30">
                    <td className="py-3 px-4 font-medium text-foreground">{order.orderNumber}</td>
                    <td className="py-3 px-4">
                      <div className="text-foreground">{order.user?.name || order.name}</div>
                      <div className="text-xs text-muted-foreground">{order.email}</div>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground">{order.package}</td>
                    <td className="py-3 px-4 text-muted-foreground">
                      {order.billingCycle === 'yearly' ? 'Tahunan' : 'Bulanan'}
                    </td>
                    <td className="py-3 px-4 text-muted-foreground">{order.domain || order.cpDomain || '-'}</td>
                    <td className="py-3 px-4 text-foreground">
                      Rp {order.totalAmount.toLocaleString('id-ID')}
                    </td>
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
                    <td className="py-3 px-4">
                      <select
                        value={order.status}
                        onChange={(e) => updateStatus(order.id, e.target.value)}
                        className="bg-muted border border-border rounded px-2 py-1 text-xs text-foreground"
                      >
                        <option value="pending">Pending</option>
                        <option value="confirmed">Confirmed</option>
                        <option value="active">Active</option>
                        <option value="suspended">Suspended</option>
                        <option value="cancelled">Cancelled</option>
                        <option value="expired">Expired</option>
                      </select>
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
