"use client";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import Sidebar from "@/components/sidebar";

class ErrorBoundary extends React.Component<React.PropsWithChildren, { hasError: boolean; error: Error | null }> {
  state = { hasError: false, error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { hasError: true, error }; }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("[ErrorBoundary]", error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, color: '#f87171', background: '#0f172a', minHeight: '100vh' }}>
          <h2 style={{ fontSize: 20, marginBottom: 12 }}>Client Error</h2>
          <pre style={{ fontSize: 13, whiteSpace: 'pre-wrap', wordBreak: 'break-word', color: '#94a3b8' }}>
            {this.state.error?.message}
            {"\n\n"}{this.state.error?.stack}
          </pre>
          <button onClick={() => this.setState({ hasError: false, error: null })} style={{ marginTop: 16, padding: '8px 16px', background: '#059669', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer' }}>
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  useEffect(() => { if (!loading && !user) router.replace("/login"); }, [user, loading, router]);
  if (loading || !mounted) return <div className="min-h-screen flex items-center justify-center bg-surface-950"><div className="animate-pulse text-brand-500 text-lg">Loading...</div></div>;
  if (!user) return null;
  return (<div className="min-h-screen bg-surface-950 flex"><Sidebar user={user} onLogout={logout}/><main className="flex-1 min-w-0"><div className="p-4 lg:p-8 pt-16 lg:pt-8 max-w-7xl mx-auto"><ErrorBoundary>{children}</ErrorBoundary></div></main></div>);
}
