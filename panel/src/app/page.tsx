"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
export default function Home() {
  const router = useRouter();
  useEffect(() => {
    const auth = localStorage.getItem("zaydpanel_auth");
    router.replace(auth ? "/admin" : "/login");
  }, [router]);
  return <div className="min-h-screen flex items-center justify-center bg-surface-950"><div className="animate-pulse text-brand-500 text-lg font-medium">ZaydPanel</div></div>;
}
