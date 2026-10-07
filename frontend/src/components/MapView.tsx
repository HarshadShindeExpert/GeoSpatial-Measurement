import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import axios from 'axios';
import { api } from '../services/api';
import { GeoJSONFeatureCollection } from '../types';
import { Map as MapIcon, Loader2, Globe, Search, MapPin, X, Compass } from 'lucide-react';

interface MapViewProps {
  fileId: string | null;
  filename?: string;
}

interface SearchResult {
  place_id: number;
  display_name: string;
  lat: string;
  lon: string;
  type: string;
}

// Custom search marker icon
const searchIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Helper to handle flyTo map navigation
const MapFlyTo: React.FC<{ coords: [number, number] | null }> = ({ coords }) => {
  const map = useMap();

  useEffect(() => {
    if (coords) {
      map.flyTo(coords, 14, {
        duration: 1.5
      });
    }
  }, [coords, map]);

  return null;
};

// Helper to auto fit bounds of uploaded dataset
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

  // Location search states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<{ coords: [number, number]; name: string } | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

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

  // Geocoding Nominatim Search
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!query.trim() || query.length < 2) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    setSearching(true);
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const response = await axios.get(`https://nominatim.openstreetmap.org/search`, {
          params: {
            q: query,
            format: 'json',
            addressdetails: 1,
            limit: 5
          },
          headers: {
            'Accept-Language': 'en'
          }
        });
        setSearchResults(response.data || []);
        setShowDropdown(true);
      } catch (err) {
        console.error('Geocoding search failed:', err);
      } finally {
        setSearching(false);
      }
    }, 400);
  };

  const handleSelectLocation = (result: SearchResult) => {
    const lat = parseFloat(result.lat);
    const lon = parseFloat(result.lon);
    setSelectedLocation({
      coords: [lat, lon],
      name: result.display_name
    });
    setSearchQuery(result.display_name.split(',')[0]);
    setShowDropdown(false);
  };

  const clearLocationSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setSelectedLocation(null);
    setShowDropdown(false);
  };

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
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl flex flex-col h-[560px] relative">
      {/* Header bar */}
      <div className="px-5 py-3.5 border-b border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/90 backdrop-blur z-10">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2 shrink-0">
          <Globe className="w-4 h-4 text-sky-400" />
          GIS Map {filename ? `— ${filename}` : ''}
        </h3>

        {/* Location Search Bar */}
        <div className="relative w-full sm:w-72">
          <div className="relative flex items-center">
            <Search className="w-4 h-4 text-slate-400 absolute left-3" />
            <input
              type="text"
              placeholder="Search places, cities, addresses..."
              value={searchQuery}
              onChange={handleSearchChange}
              onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-8 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 placeholder-slate-500"
            />
            {searching ? (
              <Loader2 className="w-3.5 h-3.5 text-sky-400 animate-spin absolute right-2.5" />
            ) : searchQuery ? (
              <button
                onClick={clearLocationSearch}
                className="p-1 text-slate-400 hover:text-white absolute right-1.5"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            ) : null}
          </div>

          {/* Autocomplete Dropdown */}
          {showDropdown && searchResults.length > 0 && (
            <div className="absolute left-0 right-0 top-full mt-1 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl z-[2000] overflow-hidden max-h-56 overflow-y-auto divide-y divide-slate-800">
              {searchResults.map((res) => (
                <div
                  key={res.place_id}
                  onClick={() => handleSelectLocation(res)}
                  className="p-2.5 hover:bg-slate-800 cursor-pointer flex items-start gap-2 transition-colors"
                >
                  <MapPin className="w-4 h-4 text-violet-400 shrink-0 mt-0.5" />
                  <div className="text-xs text-slate-200 line-clamp-2">{res.display_name}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Layer Mode Switcher */}
        <div className="flex items-center gap-3 shrink-0">
          {loading && (
            <span className="text-xs text-sky-400 flex items-center gap-1">
              <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading vector features...
            </span>
          )}

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

      {/* Map Container */}
      <div className="flex-1 w-full h-full relative">
        <MapContainer
          center={[28.6139, 77.2090]}
          zoom={12}
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

          {/* Map FlyTo animation for location search */}
          <MapFlyTo coords={selectedLocation ? selectedLocation.coords : null} />

          {/* Searched Location Marker */}
          {selectedLocation && (
            <Marker position={selectedLocation.coords} icon={searchIcon}>
              <Popup>
                <div className="p-1 max-w-xs">
                  <div className="font-bold text-violet-400 text-xs flex items-center gap-1 mb-1">
                    <Compass className="w-3.5 h-3.5" /> Searched Location
                  </div>
                  <div className="text-xs text-slate-200">{selectedLocation.name}</div>
                  <div className="text-[10px] text-slate-500 font-mono mt-1">
                    Lat: {selectedLocation.coords[0].toFixed(5)}, Lon: {selectedLocation.coords[1].toFixed(5)}
                  </div>
                </div>
              </Popup>
            </Marker>
          )}

          {/* GeoJSON Layers */}
          {geoJsonData && (
            <>
              <GeoJSON
                key={`${fileId || 'empty'}_${mapMode}`}
                data={geoJsonData as any}
                style={styleFeature}
                onEachFeature={onEachFeature}
              />
              {!selectedLocation && <FitBounds data={geoJsonData} />}
            </>
          )}
        </MapContainer>

        {!fileId && !selectedLocation && (
          <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center z-[1000] p-6 text-center">
            <Globe className="w-12 h-12 text-slate-700 mb-3" />
            <p className="text-sm text-slate-300 font-medium">No Dataset Selected</p>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              Upload a .kml or .zip Shapefile, select a dataset, or use the Location Search Bar above to navigate anywhere in the world.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
