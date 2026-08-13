"use client";
import { useState, useEffect, useCallback } from "react";
import { api, FileItem } from "@/lib/api";
import { useParams } from "next/navigation";
import {
  ArrowLeft, File, Folder, Trash2, Edit3, Save, X,
  Upload, FolderPlus, PenSquare, Search, Download, ChevronRight,
  Home
} from "lucide-react";
import Link from "next/link";

export default function FilesPage() {
  const params = useParams();
  const domain = decodeURIComponent(params.domain as string);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [currentPath, setCurrentPath] = useState("/");
  const [loading, setLoading] = useState(true);
  const [editFile, setEditFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [showMkdir, setShowMkdir] = useState(false);
  const [showRename, setShowRename] = useState(false);
  const [renameOld, setRenameOld] = useState("");
  const [renameNew, setRenameNew] = useState("");
  const [mkdirName, setMkdirName] = useState("");
  const [search, setSearch] = useState("");
  const [action, setAction] = useState<string | null>(null);
  const [result, setResult] = useState<{ success: boolean; msg: string } | null>(null);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    const res = await api.listFiles(domain, currentPath);
    if (res.success && res.data) setFiles(res.data.files || []);
    setLoading(false);
  }, [domain, currentPath]);

  useEffect(() => { fetchFiles(); }, [fetchFiles]);

  const showMessage = (success: boolean, msg: string) => {
    setResult({ success, msg });
    setTimeout(() => setResult(null), 5000);
  };

  const openFile = async (path: string) => {
    const res = await api.readFile(domain, path);
    if (res.success && res.data) {
      setFileContent(res.data.content);
      setEditFile(path);
    } else {
      showMessage(false, res.error || "Gagal membaca file");
    }
  };

  const saveFile = async () => {
    if (!editFile) return;
    const res = await api.saveFile(domain, editFile, fileContent);
    showMessage(!!res.success, res.success ? "File berhasil disimpan!" : (res.error || "Gagal"));
    setEditFile(null);
    fetchFiles();
  };

  const deleteItem = async (path: string) => {
    if (!confirm(`Hapus ${path}?`)) return;
    const res = await api.deleteFile(domain, path);
    showMessage(!!res.success, res.success ? "Berhasil dihapus!" : (res.error || "Gagal"));
    if (res.success) fetchFiles();
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setAction("upload");
    const reader = new FileReader();
    reader.onload = async () => {
      const b64 = (reader.result as string).split(",")[1];
      const res = await api.uploadFile(domain, currentPath, b64);
      showMessage(!!res.success, res.success ? `${f.name} berhasil diupload!` : (res.error || "Gagal"));
      setAction(null);
      setShowUpload(false);
      if (res.success) fetchFiles();
    };
    reader.readAsDataURL(f);
  };

  const handleMkdir = async () => {
    if (!mkdirName) return;
    const dirPath = currentPath === "/" ? `/${mkdirName}` : `${currentPath}/${mkdirName}`;
    setAction("mkdir");
    const res = await api.createDirectory(domain, dirPath);
    showMessage(!!res.success, res.success ? `Folder ${mkdirName} berhasil dibuat!` : (res.error || "Gagal"));
    setAction(null);
    setMkdirName("");
    setShowMkdir(false);
    if (res.success) fetchFiles();
  };

  const handleRename = async () => {
    if (!renameNew) return;
    setAction("rename");
    const res = await api.renameFile(domain, renameOld, renameNew);
    showMessage(!!res.success, res.success ? "Berhasil di-rename!" : (res.error || "Gagal"));
    setAction(null);
    setShowRename(false);
    if (res.success) fetchFiles();
  };

  const handleDownload = async (path: string) => {
    const res = await api.readFile(domain, path);
    if (res.success && res.data) {
      const b = new Blob([res.data.content], { type: "application/octet-stream" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(b);
      a.download = path.split("/").pop() || "file";
      a.click();
    }
  };

  const filtered = search ? files.filter(f => f.name.toLowerCase().includes(search.toLowerCase())) : files;
  const dirs = filtered.filter(f => f.type === "dir").sort((a, b) => a.name.localeCompare(b.name));
  const fileItems = filtered.filter(f => f.type === "file").sort((a, b) => a.name.localeCompare(b.name));
  const sorted = [...dirs, ...fileItems];

  const pathParts = currentPath.split("/").filter(Boolean);

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      <Link href="/admin/sites" className="inline-flex items-center gap-2 text-surface-400 hover:text-white text-sm mb-2">
        <ArrowLeft size={16} /> Kembali ke Websites
      </Link>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold text-white">Files</h1>
          <span className="text-surface-400">— {domain}</span>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowMkdir(true)} className="btn-secondary text-xs">
            <FolderPlus size={14} /> New Folder
          </button>
          <button onClick={() => setShowUpload(true)} className="btn-primary text-xs">
            <Upload size={14} /> Upload
          </button>
        </div>
      </div>

      {result && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${result.success ? "bg-brand-900/30 border border-brand-800/50 text-brand-400" : "bg-red-900/30 border border-red-800/50 text-red-400"}`}>
          {result.success ? "✓" : "✗"} {result.msg}
          <button onClick={() => setResult(null)} className="ml-auto opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      {/* Editor */}
      {editFile && (
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-white font-medium font-mono">{editFile}</span>
            <div className="flex gap-2">
              <button onClick={saveFile} className="btn-primary text-xs"><Save size={14} /> Save</button>
              <button onClick={() => setEditFile(null)} className="btn-ghost text-xs"><X size={14} /></button>
            </div>
          </div>
          <textarea
            value={fileContent}
            onChange={e => setFileContent(e.target.value)}
            className="w-full h-64 bg-surface-950 text-surface-200 text-sm font-mono p-3 rounded-lg border border-surface-700 focus:border-brand-500 focus:outline-none resize-y"
          />
        </div>
      )}

      {/* Upload Modal */}
      {showUpload && (
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white">Upload File</h3>
            <button onClick={() => setShowUpload(false)} className="btn-ghost text-xs"><X size={14} /></button>
          </div>
          <label className="block w-full border-2 border-dashed border-surface-700 rounded-lg p-8 text-center cursor-pointer hover:border-brand-500 transition-colors">
            <Upload size={32} className="mx-auto text-surface-500 mb-3" />
            <p className="text-sm text-surface-400">Klik atau drag file untuk upload</p>
            <p className="text-xs text-surface-600 mt-1">Upload ke: {currentPath}</p>
            <input type="file" onChange={handleUpload} className="hidden" />
          </label>
        </div>
      )}

      {/* Mkdir Modal */}
      {showMkdir && (
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white">Buat Folder Baru</h3>
            <button onClick={() => setShowMkdir(false)} className="btn-ghost text-xs"><X size={14} /></button>
          </div>
          <div className="flex gap-3">
            <input type="text" value={mkdirName} onChange={e => setMkdirName(e.target.value)} className="input flex-1" placeholder="Nama folder" autoFocus onKeyDown={e => e.key === "Enter" && handleMkdir()} />
            <button onClick={handleMkdir} disabled={action === "mkdir" || !mkdirName} className="btn-primary text-xs">
              {action === "mkdir" ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><FolderPlus size={14} /> Buat</>}
            </button>
          </div>
        </div>
      )}

      {/* Rename Modal */}
      {showRename && (
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white">Rename</h3>
            <button onClick={() => setShowRename(false)} className="btn-ghost text-xs"><X size={14} /></button>
          </div>
          <div className="flex gap-3">
            <input type="text" value={renameNew} onChange={e => setRenameNew(e.target.value)} className="input flex-1" placeholder="Nama baru" autoFocus onKeyDown={e => e.key === "Enter" && handleRename()} />
            <button onClick={handleRename} disabled={action === "rename" || !renameNew} className="btn-primary text-xs">
              {action === "rename" ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><PenSquare size={14} /> Rename</>}
            </button>
          </div>
        </div>
      )}

      {/* File Browser */}
      <div className="card">
        {/* Path Breadcrumb */}
        <div className="flex items-center gap-1 mb-4 text-sm flex-wrap">
          <button onClick={() => setCurrentPath("/")} className="text-surface-400 hover:text-white flex items-center gap-1">
            <Home size={14} /> /
          </button>
          {pathParts.map((part, i) => {
            const path = "/" + pathParts.slice(0, i + 1).join("/");
            return (
              <span key={path} className="flex items-center gap-1">
                <ChevronRight size={12} className="text-surface-600" />
                <button onClick={() => setCurrentPath(path)} className="text-surface-400 hover:text-white">
                  {part}
                </button>
              </span>
            );
          })}
        </div>

        {/* Search */}
        <div className="flex items-center gap-2 mb-4">
          <Search size={16} className="text-surface-400" />
          <input type="text" value={search} onChange={e => setSearch(e.target.value)} className="input flex-1" placeholder="Cari file/folder..." />
        </div>

        {/* File List Header */}
        <div className="grid grid-cols-12 gap-2 px-3 py-2 text-xs font-medium text-surface-500 border-b border-surface-800">
          <div className="col-span-6">Name</div>
          <div className="col-span-2">Size</div>
          <div className="col-span-3">Modified</div>
          <div className="col-span-1">Actions</div>
        </div>

        {/* File List */}
        {loading ? (
          <div className="animate-pulse text-surface-500 py-4">Loading...</div>
        ) : sorted.length === 0 ? (
          <p className="text-surface-500 text-sm py-4 text-center">Kosong</p>
        ) : (
          <div className="divide-y divide-surface-800/50">
            {sorted.map(f => (
              <div key={f.path} className="grid grid-cols-12 gap-2 px-3 py-2.5 hover:bg-surface-800/50 rounded-lg group items-center transition-colors">
                <div className="col-span-6 flex items-center gap-3 min-w-0">
                  <button onClick={() => f.type === "dir" ? setCurrentPath(f.path) : openFile(f.path)} className="flex items-center gap-3 text-sm">
                    {f.type === "dir" ? <Folder size={16} className="text-brand-400 flex-shrink-0" /> : <File size={16} className="text-surface-400 flex-shrink-0" />}
                    <span className="text-white truncate">{f.name}</span>
                  </button>
                </div>
                <div className="col-span-2 text-xs text-surface-500">{f.type === "file" ? formatSize(f.size) : "-"}</div>
                <div className="col-span-3 text-xs text-surface-600">
                  {f.modified ? new Date(f.modified).toLocaleString("id-ID", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }) : "-"}
                </div>
                <div className="col-span-1 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {f.type === "file" && (
                    <>
                      <button onClick={() => openFile(f.path)} className="p-1 text-surface-400 hover:text-white" title="Edit"><Edit3 size={13} /></button>
                      <button onClick={() => handleDownload(f.path)} className="p-1 text-surface-400 hover:text-white" title="Download"><Download size={13} /></button>
                    </>
                  )}
                  <button onClick={() => { setRenameOld(f.path); setRenameNew(f.name); setShowRename(true); }} className="p-1 text-surface-400 hover:text-white" title="Rename"><PenSquare size={13} /></button>
                  <button onClick={() => deleteItem(f.path)} className="p-1 text-red-400 hover:text-red-300" title="Delete"><Trash2 size={13} /></button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
