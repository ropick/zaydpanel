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

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = getStored();
    if (stored) {
      setUser(stored.user);
      setToken(stored.token);
      // Validate token with agent
      fetch("/api/agent/auth/me", {
        headers: { "Authorization": `Bearer ${stored.token}`, "Content-Type": "application/json" },
      }).then(res => {
        if (!res.ok) {
          clearStored();
          setUser(null);
          setToken(null);
        }
      }).catch(() => {});
    }
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
