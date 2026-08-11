'use client';

import { useEffect, useState } from 'react';

export default function AdminInvoicesPage() {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  const fetchInvoices = (status?: string) => {
    setLoading(true);
    const url = status ? `/api/admin/invoices?status=${status}` : '/api/admin/invoices';
    fetch(url)
      .then((r) => r.json())
      .then((d) => {
        if (d.success) setInvoices(d.invoices);
      })
      .catch((err) => console.error('Invoices fetch error:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchInvoices(filter || undefined);
  }, [filter]);

  const markPaid = async (invoiceId: string) => {
    try {
      const res = await fetch('/api/admin/invoices', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ invoiceId, status: 'paid', paymentMethod: 'manual' }),
      });
      const data = await res.json();
      if (data.success) fetchInvoices(filter || undefined);
    } catch (err) {
      console.error('Mark paid error:', err);
    }
  };

  if (loading) {
    return <div className="text-center py-20 text-muted-foreground">Memuat...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-foreground">Invoice</h1>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="bg-muted border border-border rounded-lg px-3 py-2 text-sm text-foreground"
        >
          <option value="">Semua</option>
          <option value="unpaid">Belum Dibayar</option>
          <option value="paid">Dibayar</option>
          <option value="overdue">Terlambat</option>
          <option value="cancelled">Dibatalkan</option>
        </select>
      </div>

      <div className="bg-card border border-border rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">No. Invoice</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Pelanggan</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Paket</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Jumlah</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Status</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Jatuh Tempo</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {invoices.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-muted-foreground">
                    Belum ada invoice
                  </td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id} className="border-b border-border hover:bg-muted/30">
                    <td className="py-3 px-4 font-medium text-foreground">{inv.invoiceNumber}</td>
                    <td className="py-3 px-4">
                      <div className="text-foreground">{inv.user?.name}</div>
                      <div className="text-xs text-muted-foreground">{inv.user?.email}</div>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground">{inv.order?.package}</td>
                    <td className="py-3 px-4 text-foreground">
                      Rp {inv.totalAmount.toLocaleString('id-ID')}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          inv.status === 'paid'
                            ? 'bg-green-500/20 text-green-400'
                            : inv.status === 'unpaid'
                            ? 'bg-red-500/20 text-red-400'
                            : inv.status === 'overdue'
                            ? 'bg-orange-500/20 text-orange-400'
                            : 'bg-muted text-muted-foreground'
                        }`}
                      >
                        {inv.status === 'paid'
                          ? 'Dibayar'
                          : inv.status === 'unpaid'
                          ? 'Belum Dibayar'
                          : inv.status === 'overdue'
                          ? 'Terlambat'
                          : inv.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-muted-foreground">
                      {new Date(inv.dueDate).toLocaleDateString('id-ID')}
                    </td>
                    <td className="py-3 px-4">
                      {inv.status === 'unpaid' && (
                        <button
                          onClick={() => markPaid(inv.id)}
                          className="px-3 py-1 bg-green-600/20 text-green-400 border border-green-500/30 rounded text-xs hover:bg-green-600/30 transition-colors"
                        >
                          Tandai Dibayar
                        </button>
                      )}
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
