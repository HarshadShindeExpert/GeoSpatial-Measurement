import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import { api } from '../services/api';
import { GeoJSONFeatureCollection } from '../types';
import { Map as MapIcon, Loader2, Maximize2 } from 'lucide-react';

interface MapViewProps {
  fileId: string | null;
  filename?: string;
}

// Auto fit bounds helper component
const FitBounds: React.FC<{ data: GeoJSONFeatureCollection | null }> = ({ data }) => {
  const map = useMap();

  useEffect(() => {
    if (data && data.features && data.features.length > 0) {
      try {
        const geoLayer = L.geoJSON(data as any);
        const bounds = geoLayer.getBounds();
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [40, 40] });
        }
      } catch (err) {
        console.warn('Could not fit map bounds:', err);
      }
    }
  }, [data, map]);

  return null;
};

export const MapView: React.FC<MapViewProps> = ({ fileId, filename }) => {
  const [geoJsonData, setGeoJsonData] = useState<GeoJSONFeatureCollection | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!fileId) {
      setGeoJsonData(null);
      return;
    }

    let isMounted = true;
    setLoading(true);

    api.getGeoJSON(fileId)
      .then((data) => {
        if (isMounted) {
          setGeoJsonData(data);
        }
      })
      .catch((err) => {
        console.error('Failed to load GeoJSON map data:', err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [fileId]);

  const styleFeature = (feature: any) => {
    const geomType = feature?.properties?._geometry_type || feature?.geometry?.type;
    
    if (geomType === 'Polygon' || geomType === 'MultiPolygon') {
      return {
        fillColor: '#0d9488',
        fillOpacity: 0.45,
        color: '#14b8a6',
        weight: 2,
      };
    } else if (geomType === 'LineString' || geomType === 'MultiLineString') {
      return {
        color: '#f59e0b',
        weight: 4,
        opacity: 0.85,
      };
    }
    return {
      fillColor: '#ef4444',
      color: '#dc2626',
      weight: 2,
      radius: 6,
    };
  };

  const onEachFeature = (feature: any, layer: L.Layer) => {
    const props = feature.properties || {};
    const geomType = props._geometry_type || feature.geometry?.type;
    const area = props._area_sq_m;
    const hectares = props._area_hectares;
    const length = props._length_m;
    const lengthKm = props._length_km;

    let content = `<div class="p-2 min-w-[200px]">
      <div class="font-bold text-emerald-400 text-sm border-b border-slate-700 pb-1 mb-2 flex items-center justify-between">
        <span>${geomType}</span>
        <span class="text-xs text-slate-400 font-mono">#${props._feature_index ?? 0}</span>
      </div>`;

    if (area !== null && area !== undefined) {
      content += `<div class="text-xs text-slate-200 mb-1">
        <strong>Area:</strong> ${area.toLocaleString()} m² 
        <span class="text-emerald-300">(${hectares} ha)</span>
      </div>`;
    }

    if (length !== null && length !== undefined) {
      content += `<div class="text-xs text-slate-200 mb-2">
        <strong>Length:</strong> ${length.toLocaleString()} m 
        <span class="text-amber-300">(${lengthKm} km)</span>
      </div>`;
    }

    // Properties preview
    content += `<div class="text-[11px] text-slate-400 bg-slate-900/90 p-2 rounded border border-slate-800 font-mono overflow-x-auto max-h-24">`;
    const cleanProps = { ...props };
    delete cleanProps._measurement_status;
    delete cleanProps._area_sq_m;
    delete cleanProps._area_hectares;
    delete cleanProps._length_m;
    delete cleanProps._length_km;
    delete cleanProps._geometry_type;
    delete cleanProps._feature_index;

    for (const [k, v] of Object.entries(cleanProps)) {
      content += `<div><span class="text-slate-500">${k}:</span> ${v}</div>`;
    }
    content += `</div></div>`;

    layer.bindPopup(content);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl flex flex-col h-[520px] relative">
      <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/80 backdrop-blur z-10">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <MapIcon className="w-4 h-4 text-emerald-400" />
          GIS Map Visualization {filename ? `— ${filename}` : ''}
        </h3>
        {loading && (
          <span className="text-xs text-emerald-400 flex items-center gap-1">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading vector features...
          </span>
        )}
      </div>

      <div className="flex-1 w-full h-full relative">
        <MapContainer
          center={[28.6139, 77.2090]}
          zoom={12}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {geoJsonData && (
            <>
              <GeoJSON
                key={fileId || 'empty'}
                data={geoJsonData as any}
                style={styleFeature}
                onEachFeature={onEachFeature}
              />
              <FitBounds data={geoJsonData} />
            </>
          )}
        </MapContainer>

        {!fileId && (
          <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center z-[1000] p-6 text-center">
            <MapIcon className="w-12 h-12 text-slate-700 mb-3" />
            <p className="text-sm text-slate-300 font-medium">No Dataset Selected</p>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              Upload a .kml or .zip Shapefile or select a dataset from the list to render interactive map geometries.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
