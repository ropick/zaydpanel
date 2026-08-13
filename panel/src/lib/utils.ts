export function cn(...classes: (string | boolean | undefined)[]) { return classes.filter(Boolean).join(" "); }
export function formatBytes(bytes: number) { if (bytes === 0) return "0 B"; const k = 1024; const s = ["B","KB","MB","GB","TB"]; const i = Math.floor(Math.log(bytes)/Math.log(k)); return parseFloat((bytes/Math.pow(k,i)).toFixed(1))+" "+s[i]; }
export function formatDate(d: string) { return new Date(d).toLocaleDateString("id-ID",{year:"numeric",month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"}); }
