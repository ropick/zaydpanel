"use client";
import { useState, useEffect, useCallback } from "react";

export interface User { username: string; role: "admin" | "customer"; displayName: string; }
const AUTH_KEY = "zaydpanel_auth";
const ADMIN_USER: User = { username: "admin", role: "admin", displayName: "Administrator" };

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  try { const d = localStorage.getItem(AUTH_KEY); return d ? JSON.parse(d) : null; } catch { return null; }
}
export function setStoredUser(u: User) { localStorage.setItem(AUTH_KEY, JSON.stringify(u)); }
export function clearStoredUser() { localStorage.removeItem(AUTH_KEY); }

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { setUser(getStoredUser()); setLoading(false); }, []);

  const login = useCallback((username: string, password: string): boolean => {
    const pass = process.env.NEXT_PUBLIC_ADMIN_PASSWORD || "zaydpanel2026";
    if (username === "admin" && password === pass) {
      const u: User = { ...ADMIN_USER };
      setStoredUser(u); setUser(u); return true;
    }
    return false;
  }, []);

  const logout = useCallback(() => { clearStoredUser(); setUser(null); window.location.href = "/login"; }, []);

  return { user, loading, login, logout, isAdmin: user?.role === "admin" };
}
