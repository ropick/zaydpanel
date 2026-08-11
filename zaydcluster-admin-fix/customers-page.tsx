'use client';

import { useEffect, useState } from 'react';

export default function AdminCustomersPage() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const url = search
      ? `/api/admin/customers?search=${encodeURIComponent(search)}`
      : '/api/admin/customers';
    fetch(url)
      .then((r) => r.json())
      .then((d) => {
        if (d.success) setCustomers(d.customers);
      })
      .catch((err) => console.error('Customers fetch error:', err))
      .finally(() => setLoading(false));
  }, [search]);

  if (loading) {
    return <div className="text-center py-20 text-muted-foreground">Memuat...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold text-foreground">Pelanggan</h1>
        <input
          type="text"
          placeholder="Cari pelanggan..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-muted border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
      </div>

      <div className="bg-card border border-border rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Nama</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Email</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Telepon</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Pesanan</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Invoice</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Terdaftar</th>
              </tr>
            </thead>
            <tbody>
              {customers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-muted-foreground">
                    Belum ada pelanggan
                  </td>
                </tr>
              ) : (
                customers.map((c) => (
                  <tr key={c.id} className="border-b border-border hover:bg-muted/30">
                    <td className="py-3 px-4 font-medium text-foreground">{c.name}</td>
                    <td className="py-3 px-4 text-muted-foreground">{c.email}</td>
                    <td className="py-3 px-4 text-muted-foreground">{c.phone || '-'}</td>
                    <td className="py-3 px-4 text-foreground">{c.orders?.length || 0}</td>
                    <td className="py-3 px-4 text-foreground">{c.invoices?.length || 0}</td>
                    <td className="py-3 px-4 text-muted-foreground">
                      {new Date(c.createdAt).toLocaleDateString('id-ID')}
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
