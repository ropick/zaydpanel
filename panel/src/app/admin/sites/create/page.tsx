"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { ArrowLeft, Globe, CheckCircle } from "lucide-react";
import Link from "next/link";

export default function CreateSitePage() {
  const router = useRouter();
  const [domain, setDomain] = useState("");
  const [owner, setOwner] = useState("");
  const [email, setEmail] = useState("");
  const [pkg, setPkg] = useState("Starter");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true); setResult(null);
    const res = await api.createSite(domain, owner, pkg, email);
    setResult({ success: !!res.success, msg: res.success ? `Website ${domain} berhasil dibuat!` : (res.error || "Gagal") });
    setLoading(false);
    if (res.success) setTimeout(() => router.push("/admin/sites"), 1500);
  };

  return (
    <div className="max-w-2xl">
      <Link href="/admin/sites" className="inline-flex items-center gap-2 text-surface-400 hover:text-white text-sm mb-6"><ArrowLeft size={16}/> Kembali</Link>
      <h1 className="text-2xl font-bold text-white mb-6">Buat Website Baru</h1>
      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div><label className="label">Domain</label><input type="text" value={domain} onChange={e=>setDomain(e.target.value)} className="input" placeholder="example.com" required/></div>
          <div><label className="label">Pemilik</label><input type="text" value={owner} onChange={e=>setOwner(e.target.value)} className="input" placeholder="Nama Pemilik"/></div>
          <div><label className="label">Email</label><input type="email" value={email} onChange={e=>setEmail(e.target.value)} className="input" placeholder="email@example.com"/></div>
          <div><label className="label">Paket</label><select value={pkg} onChange={e=>setPkg(e.target.value)} className="input"><option>Starter</option><option>Business</option><option>Premium</option></select></div>
          {result && <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${result.success?"bg-brand-900/30 border border-brand-800/50 text-brand-400":"bg-red-900/30 border border-red-800/50 text-red-400"}`}>{result.success?<CheckCircle size={16}/>:"✗"} {result.msg}</div>}
          <button type="submit" disabled={loading||!domain} className="btn-primary w-full">{loading?<div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>:"Buat Website"}</button>
        </form>
      </div>
    </div>
  );
}
