import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap, LayersControl } from 'react-leaflet';
import L from 'leaflet';
import { api } from '../services/api';
import { GeoJSONFeatureCollection } from '../types';
import { Map as MapIcon, Loader2, Globe, Eye } from 'lucide-react';

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
  const [mapMode, setMapMode] = useState<'satellite' | 'street'>('satellite');

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
        fillColor: '#38bdf8',
        fillOpacity: 0.45,
        color: '#0284c7',
        weight: 2.5,
      };
    } else if (geomType === 'LineString' || geomType === 'MultiLineString') {
      return {
        color: '#fbbf24',
        weight: 4,
        opacity: 0.9,
      };
    }
    return {
      fillColor: '#f43f5e',
      color: '#e11d48',
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
      <div class="font-bold text-sky-400 text-sm border-b border-slate-700 pb-1 mb-2 flex items-center justify-between">
        <span>${geomType}</span>
        <span class="text-xs text-slate-400 font-mono">#${props._feature_index ?? 0}</span>
      </div>`;

    if (area !== null && area !== undefined) {
      content += `<div class="text-xs text-slate-200 mb-1">
        <strong>Area:</strong> ${area.toLocaleString()} m² 
        <span class="text-sky-300">(${hectares} ha)</span>
      </div>`;
    }

    if (length !== null && length !== undefined) {
      content += `<div class="text-xs text-slate-200 mb-2">
        <strong>Length:</strong> ${length.toLocaleString()} m 
        <span class="text-amber-300">(${lengthKm} km)</span>
      </div>`;
    }

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
          <Globe className="w-4 h-4 text-sky-400" />
          Satellite GIS Map {filename ? `— ${filename}` : ''}
        </h3>

        <div className="flex items-center gap-3">
          {loading && (
            <span className="text-xs text-sky-400 flex items-center gap-1">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading vector features...
            </span>
          )}

          {/* Map Layer Mode Toggle */}
          <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setMapMode('satellite')}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                mapMode === 'satellite'
                  ? 'bg-sky-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Satellite View
            </button>
            <button
              onClick={() => setMapMode('street')}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                mapMode === 'street'
                  ? 'bg-sky-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Street View
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 w-full h-full relative">
        <MapContainer
          center={[28.6139, 77.2090]}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
        >
          {mapMode === 'satellite' ? (
            <TileLayer
              attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              maxZoom={19}
            />
          ) : (
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
          )}

          {geoJsonData && (
            <>
              <GeoJSON
                key={`${fileId || 'empty'}_${mapMode}`}
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
            <Globe className="w-12 h-12 text-slate-700 mb-3" />
            <p className="text-sm text-slate-300 font-medium">No Dataset Selected</p>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              Upload a .kml or .zip Shapefile or select a dataset from the list to render satellite GIS geometries.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
