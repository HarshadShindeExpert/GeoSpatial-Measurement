import React, { useState, useRef } from 'react';
import { UploadCloud, FileCode, Archive, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { api } from '../services/api';

interface FileUploadProps {
  onUploadSuccess: () => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setError(null);
    setSuccessMsg(null);

    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (ext !== '.zip' && ext !== '.kml') {
      setError('Invalid file format. Please upload a .zip (Shapefile) or .kml file.');
      return;
    }

    setLoading(true);
    try {
      const res = await api.uploadFile(file);
      setSuccessMsg(`File "${file.name}" uploaded and processed! (${res.feature_count} features)`);
      onUploadSuccess();
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || 'Failed to upload and process file.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-emerald-400" />
          Upload Geospatial File
        </h2>
        <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2.5 py-1 rounded-full border border-slate-700">
          Supported: .zip (Shapefile), .kml
        </span>
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
          isDragging
            ? 'border-emerald-500 bg-emerald-950/20'
            : 'border-slate-700 hover:border-emerald-500/50 hover:bg-slate-800/40 bg-slate-950/50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".zip,.kml"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFile(e.target.files[0]);
            }
          }}
        />

        {loading ? (
          <div className="flex flex-col items-center justify-center py-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin mb-3" />
            <p className="text-sm font-medium text-emerald-400">Extracting features & calculating projected measurements...</p>
            <p className="text-xs text-slate-500 mt-1">Transforming geographic coordinates to local metric UTM zone</p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
                <Archive className="w-6 h-6" />
              </div>
              <div className="p-3 bg-sky-500/10 text-sky-400 rounded-xl border border-sky-500/20">
                <FileCode className="w-6 h-6" />
              </div>
            </div>
            <p className="text-sm font-medium text-slate-200">
              Drag & drop your Shapefile <span className="text-emerald-400 font-mono">(.zip)</span> or <span className="text-sky-400 font-mono">(.kml)</span> file here
            </p>
            <p className="text-xs text-slate-500 mt-1">or click to browse from your device (Max 50MB)</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3.5 bg-rose-950/40 border border-rose-800/60 rounded-lg flex items-center gap-2 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="mt-4 p-3.5 bg-emerald-950/40 border border-emerald-800/60 rounded-lg flex items-center gap-2 text-emerald-300 text-xs">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
    </div>
  );
};
