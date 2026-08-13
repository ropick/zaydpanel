// All API calls go through Next.js server-side proxy route
const API_BASE = "/api/agent";

interface AgentResponse<T = unknown> {
  success: boolean;
  error?: string;
  data?: T;
}

function _getAuthToken(): string {
  if (typeof window === "undefined") return "";
  try {
    const d = localStorage.getItem("zaydpanel_auth");
    if (d) { const parsed = JSON.parse(d); return parsed.token || ""; }
  } catch {}
  return "";
}

async function agentFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<AgentResponse<T>> {
  try {
    const token = _getAuthToken();
    const headers: Record<string, string> = { "Content-Type": "application/json", ...(options.headers as Record<string, string>) };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    const raw = await res.json();
    if (res.ok) {
      // Agent wraps responses as { success: true, data: <payload> }
      // Unwrap so callers get the inner payload directly
      if (raw && typeof raw === "object" && "success" in raw && "data" in raw) {
        return { success: true, data: (raw as any).data as T };
      }
      return { success: true, data: raw as T };
    }
    return { success: false, error: (raw as { error?: string })?.error || `HTTP ${res.status}` };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : "Connection failed" };
  }
}

// ── Types ──────────────────────────────────────────
export interface SiteInfo {
  domain: string; home: string; exists: boolean;
  ssl?: boolean; has_wp?: boolean; php_version?: string;
  db_name?: string; db_user?: string;
  type?: string; php_fpm?: boolean;
}
export interface CreateSiteResult {
  domain: string; username: string; home_dir: string;
  database?: { database: string; username: string; password: string; host: string; };
}
export interface ServerInfo {
  memory_total: string; memory_used: string; memory_free: string;
  disk_total: string; disk_used: string; disk_free: string;
  cpu_percent: number; cpu_cores: string; uptime: string;
  cpu_load_1m?: number; cpu_load_5m?: number; cpu_load_15m?: number;
  net_rx_total?: string; net_tx_total?: string;
  os?: string; kernel?: string; hostname?: string; server_time?: string;
  total_sites?: number; active_sites?: number;
}
export interface ProcessInfo {
  pid: number; user: string; cpu: number; mem: number; command: string;
}
export interface DatabaseInfo {
  name: string; user: string; size: string; domain?: string;
}
export interface CronJob {
  id: string; domain: string; schedule: string; command: string;
  description?: string; enabled: boolean; last_run?: string; next_run?: string;
}
export interface SSLInfo {
  domain: string; issuer: string; expires_at: string; days_left: number;
  created_at?: string; type: string;
}
export interface LogEntry {
  timestamp: string; level: string; message: string; source?: string;
}
export interface BackupInfo {
  id: string; domain: string; filename: string; size: string;
  created_at: string; type: string;
}
export interface PHPVersion {
  version: string; path: string; active: boolean;
}
export interface SystemSetting {
  key: string; value: string; description: string;
}

export interface FileItem {
  name: string; path: string; type: "file" | "dir"; size: number; modified: string;
  permissions?: string;
}

// ── API ────────────────────────────────────────────
export const api = {
  // Health
  health: () => agentFetch<{ status: string; version?: string }>("/health"),

  // Server
  serverInfo: () => agentFetch<ServerInfo>("/server-info"),
  processes: () => agentFetch<ProcessInfo[]>("/processes"),
  restartService: (service: string) =>
    agentFetch("/service/restart", { method: "POST", body: JSON.stringify({ service }) }),

  // Sites
  listSites: () => agentFetch<SiteInfo[]>("/sites"),
  createSite: (domain: string, owner: string, pkg: string, email: string) =>
    agentFetch<CreateSiteResult>("/site/create", { method: "POST", body: JSON.stringify({ domain, owner, package: pkg, email }) }),
  deleteSite: (domain: string) =>
    agentFetch("/site/delete", { method: "POST", body: JSON.stringify({ domain }) }),
  installWordPress: (domain: string, title: string, adminUser: string, adminPass?: string, adminEmail?: string) =>
    agentFetch("/wordpress/install", { method: "POST", body: JSON.stringify({ domain, title, admin_user: adminUser, admin_pass: adminPass || "", admin_email: adminEmail || "" }) }),

  // SSL
  issueSSL: (domain: string) =>
    agentFetch("/ssl/issue", { method: "POST", body: JSON.stringify({ domain }) }),
  listSSL: () => agentFetch<SSLInfo[]>("/ssl/list"),
  renewSSL: (domain: string) =>
    agentFetch("/ssl/renew", { method: "POST", body: JSON.stringify({ domain }) }),

  // Databases
  listDatabases: () => agentFetch<DatabaseInfo[]>("/db/list"),
  createDatabase: (domain: string) =>
    agentFetch("/db/create", { method: "POST", body: JSON.stringify({ domain }) }),
  deleteDatabase: (name: string) =>
    agentFetch("/db/delete", { method: "POST", body: JSON.stringify({ database: name }) }),

  // Files
  listFiles: (domain: string, path: string = "/") =>
    agentFetch<{ files: FileItem[]; path: string }>(`/files/${domain}${path}`),
  readFile: (domain: string, path: string) =>
    agentFetch<{ content: string; size: number }>(`/file-content/${domain}${path}`),
  saveFile: (domain: string, path: string, content: string) =>
    agentFetch(`/file-save/${domain}${path}`, { method: "POST", body: JSON.stringify({ content }) }),
  deleteFile: (domain: string, path: string) =>
    agentFetch(`/file-delete/${domain}${path}`, { method: "POST" }),
  uploadFile: (domain: string, path: string, contentB64: string) =>
    agentFetch(`/file-upload/${domain}${path}`, { method: "POST", body: JSON.stringify({ content_b64: contentB64 }) }),
  createDirectory: (domain: string, path: string) =>
    agentFetch(`/mkdir/${domain}${path}`, { method: "POST" }),
  renameFile: (domain: string, oldPath: string, newPath: string) =>
    agentFetch(`/rename/${domain}`, { method: "POST", body: JSON.stringify({ old_path: oldPath, new_path: newPath }) }),

  // Cron Jobs
  listCronJobs: () => agentFetch<CronJob[]>("/cron/list"),
  createCronJob: (domain: string, schedule: string, command: string, description?: string) =>
    agentFetch("/cron/create", { method: "POST", body: JSON.stringify({ domain, schedule, command, description }) }),
  deleteCronJob: (id: string) =>
    agentFetch("/cron/delete", { method: "POST", body: JSON.stringify({ id }) }),
  toggleCronJob: (id: string, enabled: boolean) =>
    agentFetch("/cron/toggle", { method: "POST", body: JSON.stringify({ id, enabled }) }),

  // Logs
  getLogs: (domain: string, type: "access" | "error", lines?: number) =>
    agentFetch<{ logs: LogEntry[]; domain: string; type: string }>(`/logs/${domain}/${type}?lines=${lines || 100}`),

  // Backups
  listBackups: () => agentFetch<BackupInfo[]>("/backup/list"),
  createBackup: (domain: string) =>
    agentFetch("/backup/create", { method: "POST", body: JSON.stringify({ domain }) }),
  restoreBackup: (id: string) =>
    agentFetch("/backup/restore", { method: "POST", body: JSON.stringify({ id }) }),
  deleteBackup: (id: string) =>
    agentFetch("/backup/delete", { method: "POST", body: JSON.stringify({ id }) }),
  downloadBackup: (id: string) =>
    agentFetch<{ url: string }>(`/backup/download/${id}`),

  // PHP
  listPHPVersions: () => agentFetch<PHPVersion[]>("/php/versions"),
  setPHPVersion: (domain: string, version: string) =>
    agentFetch("/php/set-version", { method: "POST", body: JSON.stringify({ domain, version }) }),

  // Settings
  getSettings: () => agentFetch<SystemSetting[]>("/settings"),
  updateSetting: (key: string, value: string) =>
    agentFetch("/settings/update", { method: "POST", body: JSON.stringify({ key, value }) }),

  // Auth
  login: (username: string, password: string) =>
    agentFetch<{ token: string; user: any }>("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  getMe: () => agentFetch<any>("/auth/me"),
  changePassword: (oldPassword: string, newPassword: string) =>
    agentFetch("/auth/change-password", { method: "POST", body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }) }),

  // Users (admin)
  listUsers: () => agentFetch<any[]>("/users"),
  createUser: (data: { username: string; password?: string; email?: string; full_name?: string; role?: string; package_id?: number }) =>
    agentFetch("/auth/users", { method: "POST", body: JSON.stringify(data) }),
  updateUser: (data: { id: number; [key: string]: any }) =>
    agentFetch(`/auth/users/${data.id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteUser: (id: number) =>
    agentFetch(`/auth/users/${id}`, { method: "DELETE", body: JSON.stringify({ id }) }),
  resetPassword: (id: number) =>
    agentFetch("/auth/users/reset", { method: "POST", body: JSON.stringify({ id }) }),

  // Packages (admin)
  listPackages: () => agentFetch<any[]>("/packages"),
  createPackage: (data: Record<string, any>) =>
    agentFetch("/auth/packages", { method: "POST", body: JSON.stringify(data) }),
  updatePackage: (data: Record<string, any>) =>
    agentFetch(`/auth/packages/${data.id}`, { method: "PUT", body: JSON.stringify(data) }),
  deletePackage: (id: number) =>
    agentFetch(`/auth/packages/${id}`, { method: "DELETE", body: JSON.stringify({ id }) }),

  // Email
  listEmail: () => agentFetch<any[]>("/email/list"),
  createEmail: (domain: string, address: string, password?: string, quota_mb?: number) =>
    agentFetch("/email/create", { method: "POST", body: JSON.stringify({ domain, address, password, quota_mb }) }),
  deleteEmail: (id: number) =>
    agentFetch("/email/delete", { method: "POST", body: JSON.stringify({ id }) }),

  // FTP
  listFTP: () => agentFetch<any[]>("/ftp/list"),
  createFTP: (domain: string, username: string, password?: string, home_dir?: string) =>
    agentFetch("/ftp/create", { method: "POST", body: JSON.stringify({ domain, username, password, home_dir }) }),
  deleteFTP: (id: number) =>
    agentFetch("/ftp/delete", { method: "POST", body: JSON.stringify({ id }) }),

  // App Install
  installApp: (domain: string, appType: string) =>
    agentFetch("/app/install", { method: "POST", body: JSON.stringify({ domain, app_type: appType }) }),

  // Statistics
  getStatistics: () => agentFetch<any[]>("/statistics"),
  getQuota: () => agentFetch<any>("/quota"),

  // Activity
  getActivity: () => agentFetch<any[]>("/activity"),
};
