import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "ZaydPanel - Free Multi-User Control Panel", description: "Free, open-source multi-user control panel for shared hosting management.", icons: { icon: "/favicon.ico" } };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="id" className="dark"><body className="min-h-screen bg-surface-950 text-surface-100 antialiased" suppressHydrationWarning>{children}</body></html>);
}
