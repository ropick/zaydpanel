"use client";
import { useState, useEffect, useCallback } from "react";

const AUTH_KEY = "zaydpanel_auth";

export interface User {
  id: number; username: string; role: "admin" | "customer";
  email: string; full_name: string; package_id?: number | null;
  package?: { name: string; slug: string } | null;
  status: string; created_at: string; last_login?: string;
}

interface StoredAuth { token: string; user: User; }

function getStored(): StoredAuth | null {
  if (typeof window === "undefined") return null;
  try { const d = localStorage.getItem(AUTH_KEY); return d ? JSON.parse(d) : null; } catch { return null; }
}
function setStored(a: StoredAuth) { localStorage.setItem(AUTH_KEY, JSON.stringify(a)); }
function clearStored() { localStorage.removeItem(AUTH_KEY); }

// Fallback for development/demo
const FALLBACK_ADMIN: User = {
  id: 0, username: "admin", role: "admin",
  email: "admin@localhost", full_name: "Administrator",
  package_id: null, package: null, status: "active",
  created_at: "", last_login: "",
};

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = getStored();
    if (stored) { setUser(stored.user); setToken(stored.token); }
    setLoading(false);
  }, []);

  const login = useCallback(async (username: string, password: string): Promise<boolean> => {
    try {
      const res = await fetch("/api/agent/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (data.success && data.data) {
        const { token: jwt, user: u } = data.data;
        setStored({ token: jwt, user: u });
        setUser(u); setToken(jwt);
        return true;
      }
      return false;
    } catch {
      // Fallback for development: accept hardcoded admin
      const pass = process.env.NEXT_PUBLIC_ADMIN_PASSWORD || "zaydpanel2026";
      if (username === "admin" && password === pass) {
        const auth: StoredAuth = { token: "dev-token", user: FALLBACK_ADMIN };
        setStored(auth); setUser(FALLBACK_ADMIN); setToken("dev-token");
        return true;
      }
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    clearStored(); setUser(null); setToken(null);
    window.location.href = "/login";
  }, []);

  return { user, token, loading, login, logout, isAdmin: user?.role === "admin", isCustomer: user?.role === "customer" };
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return getStored()?.token || null;
}
