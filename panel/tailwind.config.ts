import type { Config } from "tailwindcss";
const config: Config = { content: ["./src/**/*.{ts,tsx}"], theme: { extend: { colors: { brand: { 400:"#34d399",500:"#10b981",600:"#059669",700:"#047857",800:"#065f46",900:"#064e3b" }, surface: { 50:"#f8fafc",100:"#e2e8f0",200:"#cbd5e1",300:"#94a3b8",400:"#64748b",500:"#475569",600:"#334155",700:"#1e293b",800:"#0f172a",900:"#020617",950:"#010312" } } } }, plugins: [] };
export default config;
