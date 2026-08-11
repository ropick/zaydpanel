'use client';

import { useState, useEffect } from 'react';
import { signIn, useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LoginPage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  // If already logged in, redirect based on role
  useEffect(() => {
    if (status === 'authenticated' && session?.user) {
      const role = (session.user as any).role;
      if (role === 'admin') {
        router.push('/admin');
      } else {
        router.push('/dashboard');
      }
    }
  }, [status, session, router]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('passwordSet') === 'true') {
      setSuccess('Password berhasil diatur! Silakan login.');
    }
    if (params.get('registered') === 'true') {
      setSuccess('Registrasi berhasil! Silakan login.');
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await signIn('credentials', {
        email,
        password,
        redirect: false,
      });

      if (result?.error) {
        setError(result.error);
      } else {
        // Fetch user session to check role
        const res = await fetch('/api/auth/session');
        const sess = await res.json();
        const role = (sess?.user as any)?.role;
        if (role === 'admin') {
          router.push('/admin');
        } else {
          router.push('/dashboard');
        }
      }
    } catch (err) {
      setError('Terjadi kesalahan');
    } finally {
      setLoading(false);
    }
  };

  // Don't show login form if already authenticated
  if (status === 'authenticated') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-muted-foreground">Mengalihkan...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="max-w-md w-full space-y-8 p-8 bg-card border border-border rounded-xl shadow-sm">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-foreground">ZaydCluster</h1>
          <p className="mt-2 text-muted-foreground">Masuk ke akun Anda</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-6">
          {success && (
            <div className="bg-green-500/20 text-green-400 p-3 rounded-lg text-sm border border-green-500/30">
              {success}
            </div>
          )}
          {error && (
            <div className="bg-red-500/20 text-red-400 p-3 rounded-lg text-sm border border-red-500/30">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="block w-full px-4 py-2.5 bg-muted border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="email@contoh.com"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="block w-full px-4 py-2.5 bg-muted border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Masukkan password"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2.5 px-4 rounded-lg text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Masuk...' : 'Masuk'}
          </button>
        </form>
        <p className="text-center text-sm text-muted-foreground">
          Belum punya akun?{' '}
          <Link href="/register" className="text-purple-400 hover:underline">
            Daftar
          </Link>
        </p>
      </div>
    </div>
  );
}
