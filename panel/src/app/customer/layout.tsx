"use client";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";
import CustomerSidebar from "@/components/customer-sidebar";

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

export default function CustomerLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, isAdmin, logout } = useAuth();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  useEffect(() => {
    if (!loading && !mounted) return;
    // Admin should not access customer panel
    if (!loading && user && user.role === "admin" && !redirecting) {
      setRedirecting(true);
      router.replace("/admin");
      return;
    }
    // Not logged in → redirect to login
    if (!loading && !user && !redirecting) {
      setRedirecting(true);
      router.replace("/login");
    }
  }, [user, loading, router, mounted, redirecting]);

  if (!mounted || loading) return <div className="min-h-screen flex items-center justify-center bg-surface-950"><div className="animate-pulse text-brand-500 text-lg">Loading...</div></div>;
  if (!user) return null;

  return (
    <div className="min-h-screen bg-surface-950 flex">
      <CustomerSidebar user={user} onLogout={logout} />
      <main className="flex-1 min-w-0">
        <div className="p-4 lg:p-8 pt-16 lg:pt-8 max-w-7xl mx-auto">
          <ErrorBoundary>{children}</ErrorBoundary>
        </div>
      </main>
    </div>
  );
}
