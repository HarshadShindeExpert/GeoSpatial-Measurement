import React, { useEffect, useState } from 'react';
import { api } from './services/api';
import { FileItem } from './types';
import { FileUpload } from './components/FileUpload';
import { FileList } from './components/FileList';
import { MapView } from './components/MapView';
import { FileDetailsModal } from './components/FileDetailsModal';
import { Globe, BookOpen, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [modalFileId, setModalFileId] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchFiles = async () => {
    setLoading(true);
    try {
      const data = await api.listFiles();
      setFiles(data);
      setApiOnline(true);
      if (data.length > 0 && !selectedFileId) {
        setSelectedFileId(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load files:', err);
      setApiOnline(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await api.deleteFile(id);
      if (selectedFileId === id) {
        setSelectedFileId(null);
      }
      fetchFiles();
    } catch (err) {
      console.error('Failed to delete file:', err);
    }
  };

  const selectedFile = files.find((f) => f.id === selectedFileId);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
              <Globe className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                GeoMeasure <span className="text-xs font-mono bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded-full font-normal">v1.0</span>
              </h1>
              <p className="text-xs text-slate-400">Production Geospatial File Measurement Platform</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {apiOnline === true && (
              <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-3 py-1 rounded-full font-medium">
                <CheckCircle2 className="w-3.5 h-3.5" /> API Connected
              </span>
            )}
            {apiOnline === false && (
              <span className="inline-flex items-center gap-1.5 text-xs text-rose-400 bg-rose-950/60 border border-rose-800/60 px-3 py-1 rounded-full font-medium">
                <AlertCircle className="w-3.5 h-3.5" /> API Offline
              </span>
            )}

            <button
              onClick={fetchFiles}
              disabled={loading}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg border border-slate-700 transition-colors"
              title="Refresh Files"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>

            <a
              href="http://127.0.0.1:8000/api/docs"
              target="_blank"
              rel="noreferrer"
              className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 shadow-lg shadow-emerald-900/20"
            >
              <BookOpen className="w-3.5 h-3.5" />
              Swagger API Docs
            </a>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 py-8 flex-1 w-full space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Upload & File List */}
          <div className="lg:col-span-5 space-y-6">
            <FileUpload onUploadSuccess={fetchFiles} />
            <FileList
              files={files}
              selectedFileId={selectedFileId}
              onSelectFile={setSelectedFileId}
              onViewDetails={setModalFileId}
              onDeleteFile={handleDelete}
            />
          </div>

          {/* Right Column: GIS Map View */}
          <div className="lg:col-span-7">
            <MapView fileId={selectedFileId} filename={selectedFile?.filename} />
          </div>
        </div>
      </main>

      {/* Details & Measurement Modal */}
      {modalFileId && (
        <FileDetailsModal fileId={modalFileId} onClose={() => setModalFileId(null)} />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-900 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
          <p>Geospatial File Measurement API & Platform — Built with FastAPI, GeoPandas, PyProj, Shapely & React</p>
          <p className="font-mono text-slate-400">EPSG:4326 → Automatic UTM Metric Reprojection</p>
        </div>
      </footer>
    </div>
  );
};
