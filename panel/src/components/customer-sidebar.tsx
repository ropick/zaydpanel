"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Globe, Database, LogOut, Shield, Menu, X,
  PanelLeftClose, PanelLeftOpen, Lock, FileText, HardDrive,
  UserCircle, ScrollText, Mail, FolderOpen, Zap
} from "lucide-react";
import { useState } from "react";
import type { User } from "@/lib/auth";

const navItems = [
  { href: "/customer", label: "Dashboard", icon: LayoutDashboard },
  { href: "/customer/sites", label: "Website", icon: Globe },
  { href: "/customer/apps", label: "Install App", icon: Zap },
  { href: "/customer/databases", label: "Database", icon: Database },
  { href: "/customer/ssl", label: "SSL", icon: Lock },
  { href: "/customer/email", label: "Email", icon: Mail },
  { href: "/customer/ftp", label: "FTP", icon: FolderOpen },
  { href: "/customer/backups", label: "Backup", icon: HardDrive },
  { href: "/customer/logs", label: "Log", icon: ScrollText },
  { href: "/customer/profile", label: "Profile", icon: UserCircle },
];

export default function CustomerSidebar({ user, onLogout }: { user: User; onLogout: () => void }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <button onClick={() => setMobileOpen(true)} className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-surface-800 rounded-lg border border-surface-700 text-surface-300 hover:text-white">
        <Menu size={20} />
      </button>
      {mobileOpen && <div className="lg:hidden fixed inset-0 bg-black/50 z-40" onClick={() => setMobileOpen(false)} />}
      <aside className={`fixed top-0 left-0 h-full bg-surface-900 border-r border-surface-800 z-50 transition-all duration-300 flex flex-col ${collapsed ? "w-16" : "w-64"} ${mobileOpen ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}>
        {/* Header */}
        <div className={`flex items-center gap-3 p-4 border-b border-surface-800 ${collapsed ? "justify-center" : ""}`}>
          <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <Shield size={18} className="text-white" />
          </div>
          {!collapsed && (
            <div>
              <h1 className="text-sm font-bold text-white leading-tight">ZaydPanel</h1>
              <p className="text-[10px] text-surface-500 leading-tight">v3.0</p>
            </div>
          )}
          <button onClick={() => setCollapsed(!collapsed)} className="hidden lg:block ml-auto p-1 text-surface-500 hover:text-white">
            {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
          </button>
          <button onClick={() => setMobileOpen(false)} className="lg:hidden ml-auto p-1 text-surface-500 hover:text-white">
            <X size={16} />
          </button>
        </div>

        {/* Navigation - flat list, no sections */}
        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/customer" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.label}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? "bg-brand-600/20 text-brand-400 border border-brand-600/30"
                    : "text-surface-400 hover:text-white hover:bg-surface-800 border border-transparent"
                } ${collapsed ? "justify-center" : ""}`}
                title={collapsed ? item.label : undefined}
              >
                <item.icon size={18} className="flex-shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* User */}
        <div className={`p-4 border-t border-surface-800 ${collapsed ? "flex flex-col items-center" : ""}`}>
          <div className={`flex items-center ${collapsed ? "flex-col gap-2" : "gap-3"}`}>
            <div className="w-8 h-8 bg-surface-700 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-brand-400 uppercase">{user.username[0]}</span>
            </div>
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{user.full_name || user.username}</p>
                <p className="text-xs text-surface-500 capitalize">{user.role}</p>
              </div>
            )}
          </div>
          <button onClick={onLogout} className={`mt-3 flex items-center gap-2 text-surface-500 hover:text-red-400 text-sm ${collapsed ? "justify-center" : "px-0"}`}>
            <LogOut size={16} />
            {!collapsed && <span>Logout</span>}
          </button>
        </div>
      </aside>
      <div className={`hidden lg:block flex-shrink-0 transition-all ${collapsed ? "w-16" : "w-64"}`} />
    </>
  );
}
