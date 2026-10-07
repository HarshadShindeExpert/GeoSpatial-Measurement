import React from 'react';
import { FileItem } from '../types';
import { FileText, Map, Layers, Trash2, CheckCircle, Clock, AlertTriangle, ChevronRight } from 'lucide-react';

interface FileListProps {
  files: FileItem[];
  selectedFileId: string | null;
  onSelectFile: (id: string) => void;
  onViewDetails: (id: string) => void;
  onDeleteFile: (id: string) => void;
}

export const FileList: React.FC<FileListProps> = ({
  files,
  selectedFileId,
  onSelectFile,
  onViewDetails,
  onDeleteFile,
}) => {
  if (files.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center">
        <Layers className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <p className="text-sm text-slate-400 font-medium">No files uploaded yet</p>
        <p className="text-xs text-slate-600 mt-1">Upload a .kml or .zip Shapefile above to see features and metric measurements.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          Uploaded Datasets ({files.length})
        </h3>
      </div>

      <div className="divide-y divide-slate-800/60 max-h-[420px] overflow-y-auto">
        {files.map((file) => {
          const isSelected = selectedFileId === file.id;

          return (
            <div
              key={file.id}
              onClick={() => onSelectFile(file.id)}
              className={`p-4 transition-all duration-150 cursor-pointer flex flex-col gap-2 ${
                isSelected
                  ? 'bg-slate-800/80 border-l-4 border-l-emerald-400'
                  : 'hover:bg-slate-800/40 bg-slate-900'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="p-2 bg-slate-800 rounded-lg text-emerald-400 border border-slate-700 shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-100 truncate">{file.filename}</p>
                    <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-400">
                      <span className="font-mono bg-slate-800 px-1.5 py-0.5 rounded text-[11px] text-slate-300">
                        {file.file_type}
                      </span>
                      <span>•</span>
                      <span>{file.feature_count} features</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  {file.status === 'COMPLETED' && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-2 py-0.5 rounded-full">
                      <CheckCircle className="w-3 h-3" />
                      Ready
                    </span>
                  )}
                  {file.status === 'PROCESSING' && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-400 bg-amber-950/60 border border-amber-800/60 px-2 py-0.5 rounded-full">
                      <Clock className="w-3 h-3 animate-spin" />
                      Processing
                    </span>
                  )}
                  {file.status === 'FAILED' && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-rose-400 bg-rose-950/60 border border-rose-800/60 px-2 py-0.5 rounded-full">
                      <AlertTriangle className="w-3 h-3" />
                      Failed
                    </span>
                  )}
                </div>
              </div>

              {/* Detail meta badges */}
              <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1 pt-2 border-t border-slate-800/40">
                <div className="flex items-center gap-3">
                  <span>
                    CRS: <strong className="text-slate-200 font-mono">{file.crs || 'EPSG:4326'}</strong>
                  </span>
                  {file.projected_crs && (
                    <span>
                      UTM: <strong className="text-emerald-400 font-mono">{file.projected_crs}</strong>
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => onViewDetails(file.id)}
                    className="p-1.5 hover:bg-slate-700 text-slate-300 hover:text-white rounded-md transition-colors flex items-center gap-1 text-xs"
                    title="View Measurements"
                  >
                    <span>Measurements</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => onDeleteFile(file.id)}
                    className="p-1.5 hover:bg-rose-900/50 text-slate-400 hover:text-rose-400 rounded-md transition-colors"
                    title="Delete File"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
