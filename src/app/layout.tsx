import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "NusaHost - Shared Hosting Super Cepat & Terpercaya Indonesia",
  description:
    "Layanan shared hosting berkualitas tinggi dengan server Indonesia, support 24/7, SSL gratis, dan harga terjangkau mulai Rp 29.900/bulan. Cocok untuk website, blog, toko online, dan bisnis UMKM.",
  keywords: [
    "shared hosting",
    "hosting Indonesia",
    "hosting murah",
    "hosting cepat",
    "cPanel hosting",
    "NusaHost",
    "hosting Jakarta",
    "hosting Singapore",
    "web hosting",
    "domain Indonesia",
  ],
  authors: [{ name: "NusaHost" }],
  icons: {
    icon: "https://z-cdn.chatglm.cn/z-ai/static/logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id" suppressHydrationWarning className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
