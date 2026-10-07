import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { FileMeasurementsResponse, FeatureMeasurement } from '../types';
import { X, Download, Search, Filter, ShieldCheck, Ruler, Scale, Globe2, AlertCircle, RefreshCw } from 'lucide-react';

interface FileDetailsModalProps {
  fileId: string | null;
  onClose: () => void;
}

export const FileDetailsModal: React.FC<FileDetailsModalProps> = ({ fileId, onClose }) => {
  const [data, setData] = useState<FileMeasurementsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterGeom, setFilterGeom] = useState<string>('ALL');

  useEffect(() => {
    if (!fileId) return;

    setLoading(true);
    setError(null);

    api.getMeasurements(fileId)
      .then((res) => {
        setData(res);
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Failed to fetch file measurements.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [fileId]);

  if (!fileId) return null;

  const exportJSON = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${data.filename}_measurements.json`;
    a.click();
  };

  const exportCSV = () => {
    if (!data) return;
    const headers = ['Feature_Index', 'Feature_ID', 'Geometry_Type', 'Status', 'Area_sq_m', 'Area_ha', 'Area_sq_km', 'Length_m', 'Length_km', 'Geodesic_Area_sq_m', 'Notes'];
    const rows = data.features.map((f) => [
      f.feature_index,
      `"${f.feature_id || ''}"`,
      f.geometry_type,
      f.measurement_status,
      f.area?.sq_meters ?? '',
      f.area?.hectares ?? '',
      f.area?.sq_km ?? '',
      f.length?.meters ?? '',
      f.length?.kilometers ?? '',
      f.geodesic?.geodesic_area_sq_m ?? '',
      `"${(f.notes || '').replace(/"/g, '""')}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${data.filename}_measurements.csv`;
    a.click();
  };

  const filteredFeatures = (data?.features || []).filter((f) => {
    const matchesSearch =
      searchTerm === '' ||
      (f.feature_id && f.feature_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      f.geometry_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      JSON.stringify(f.properties).toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter =
      filterGeom === 'ALL' ||
      (filterGeom === 'POLYGON' && (f.geometry_type === 'Polygon' || f.geometry_type === 'MultiPolygon')) ||
      (filterGeom === 'LINE' && (f.geometry_type === 'LineString' || f.geometry_type === 'MultiLineString')) ||
      (filterGeom === 'POINT' && (f.geometry_type === 'Point' || f.geometry_type === 'MultiPoint'));

    return matchesSearch && matchesFilter;
  });

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-[2000] flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Scale className="w-5 h-5 text-emerald-400" />
              {data?.filename || 'File Measurement Analysis'}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">ID: {fileId}</p>
          </div>

          <div className="flex items-center gap-3">
            {data && (
              <>
                <button
                  onClick={exportCSV}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white rounded-lg text-xs font-medium border border-slate-700 transition-colors flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5 text-emerald-400" />
                  Export CSV
                </button>
                <button
                  onClick={exportJSON}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white rounded-lg text-xs font-medium border border-slate-700 transition-colors flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5 text-sky-400" />
                  Export JSON
                </button>
              </>
            )}
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading && (
            <div className="py-16 text-center">
              <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mx-auto mb-3" />
              <p className="text-sm text-slate-300">Fetching feature measurements...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-950/50 border border-rose-800/60 rounded-xl text-rose-300 text-sm flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {data && (
            <>
              {/* Summary Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl">
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
                    <Scale className="w-4 h-4 text-emerald-400" />
                    Total Polygon Area
                  </div>
                  <p className="text-xl font-bold text-emerald-400">
                    {data.summary.total_area_sq_m.toLocaleString()} <span className="text-xs font-normal text-slate-400">m²</span>
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {data.summary.total_area_hectares} ha ({data.summary.total_area_sq_km} km²)
                  </p>
                </div>

                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl">
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
                    <Ruler className="w-4 h-4 text-amber-400" />
                    Total Line Length
                  </div>
                  <p className="text-xl font-bold text-amber-400">
                    {data.summary.total_length_m.toLocaleString()} <span className="text-xs font-normal text-slate-400">m</span>
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {data.summary.total_length_km} km
                  </p>
                </div>

                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl">
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
                    <Globe2 className="w-4 h-4 text-sky-400" />
                    Coordinate System (CRS)
                  </div>
                  <p className="text-sm font-semibold text-slate-200 font-mono">
                    Source: {data.crs}
                  </p>
                  <p className="text-xs text-emerald-400 font-mono mt-1">
                    Projected: {data.projected_crs} (UTM)
                  </p>
                </div>

                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-xl">
                  <div className="flex items-center gap-2 text-xs font-medium text-slate-400 mb-1">
                    <ShieldCheck className="w-4 h-4 text-purple-400" />
                    Features Breakdown
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-300 mt-1 font-mono">
                    <span className="bg-emerald-950/80 text-emerald-300 px-1.5 py-0.5 rounded">{data.summary.polygon_count} Poly</span>
                    <span className="bg-amber-950/80 text-amber-300 px-1.5 py-0.5 rounded">{data.summary.linestring_count} Line</span>
                    <span className="bg-sky-950/80 text-sky-300 px-1.5 py-0.5 rounded">{data.summary.point_count} Point</span>
                  </div>
                </div>
              </div>

              {/* Filters & Search */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-950/40 p-3 rounded-xl border border-slate-800">
                <div className="relative w-full sm:w-72">
                  <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search feature ID, attributes..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div className="flex items-center gap-2 w-full sm:w-auto">
                  <Filter className="w-4 h-4 text-slate-500" />
                  <select
                    value={filterGeom}
                    onChange={(e) => setFilterGeom(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                  >
                    <option value="ALL">All Geometry Types</option>
                    <option value="POLYGON">Polygon / MultiPolygon</option>
                    <option value="LINE">LineString / MultiLineString</option>
                    <option value="POINT">Point / MultiPoint</option>
                  </select>
                </div>
              </div>

              {/* Feature Measurements Table */}
              <div className="border border-slate-800 rounded-xl overflow-hidden shadow-inner">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3">#</th>
                      <th className="px-4 py-3">ID / Identifier</th>
                      <th className="px-4 py-3">Geometry</th>
                      <th className="px-4 py-3">Metric Area</th>
                      <th className="px-4 py-3">Metric Length</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/50">
                    {filteredFeatures.map((feat) => (
                      <tr key={feat.feature_index} className="hover:bg-slate-800/40">
                        <td className="px-4 py-3 font-mono text-slate-500">{feat.feature_index}</td>
                        <td className="px-4 py-3 font-medium text-slate-100">{feat.feature_id || `feature_${feat.feature_index}`}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-[11px] font-mono text-slate-300">
                            {feat.geometry_type}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono">
                          {feat.area ? (
                            <div>
                              <span className="text-emerald-400 font-bold">{feat.area.sq_meters.toLocaleString()} m²</span>
                              <div className="text-[10px] text-slate-500">{feat.area.hectares} ha</div>
                            </div>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 font-mono">
                          {feat.length ? (
                            <div>
                              <span className="text-amber-400 font-bold">{feat.length.meters.toLocaleString()} m</span>
                              <div className="text-[10px] text-slate-500">{feat.length.kilometers} km</div>
                            </div>
                          ) : (
                            <span className="text-slate-600">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          {feat.measurement_status === 'CALCULATED' && (
                            <span className="text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded-full font-medium">
                              Calculated
                            </span>
                          )}
                          {feat.measurement_status === 'NOT_APPLICABLE' && (
                            <span className="text-[10px] bg-slate-800 text-slate-400 border border-slate-700 px-2 py-0.5 rounded-full">
                              N/A (Point)
                            </span>
                          )}
                          {feat.measurement_status === 'INVALID_GEOMETRY' && (
                            <span className="text-[10px] bg-rose-950 text-rose-400 border border-rose-800 px-2 py-0.5 rounded-full">
                              Invalid
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}

                    {filteredFeatures.length === 0 && (
                      <tr>
                        <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                          No features matching search criteria.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
