"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Shield, Eye, EyeOff, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(""); setLoading(true);
    await new Promise((r) => setTimeout(r, 500));
    const success = await login(username, password);
    if (success) {
      // Determine redirect based on role
      try {
        const stored = JSON.parse(localStorage.getItem("zaydpanel_auth") || "{}");
        const role = stored.user?.role || "admin";
        router.push(role === "admin" ? "/admin" : "/customer");
      } catch { router.push("/admin"); }
    } else { setError("Username atau password salah"); }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-surface-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-brand-600/20 rounded-2xl mb-4 ring-1 ring-brand-600/30"><Shield size={32} className="text-brand-500"/></div>
          <h1 className="text-2xl font-bold text-white">ZaydPanel</h1>
          <p className="text-surface-400 text-sm mt-1">Free Multi-User Control Panel</p>
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-6">Masuk ke Panel</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div><label className="label">Username</label><input type="text" value={username} onChange={(e)=>setUsername(e.target.value)} className="input" placeholder="admin" autoFocus required/></div>
            <div><label className="label">Password</label>
              <div className="relative"><input type={showPassword?"text":"password"} value={password} onChange={(e)=>setPassword(e.target.value)} className="input pr-10" placeholder="••••••••" required/>
                <button type="button" onClick={()=>setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-500 hover:text-surface-300">{showPassword?<EyeOff size={16}/>:<Eye size={16}/>}</button>
              </div>
            </div>
            {error && <div className="bg-red-900/30 border border-red-800/50 rounded-lg px-4 py-2.5 text-red-400 text-sm">{error}</div>}
            <button type="submit" disabled={loading||!username||!password} className="btn-primary w-full">{loading?<div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>:<>Masuk<ArrowRight size={16}/></>}</button>
          </form>
        </div>
        <p className="text-center text-surface-600 text-xs mt-6">ZaydPanel v3.0 — Free &amp; Open Source</p>
      </div>
    </div>
  );
}
