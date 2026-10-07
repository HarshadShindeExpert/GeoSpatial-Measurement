import math
import logging
from typing import Optional, Tuple
import geopandas as gpd
from pyproj import CRS, Transformer
from shapely.geometry import base, shape
from shapely.ops import transform

logger = logging.getLogger("geospatial.crs")

class CRSService:
    @staticmethod
    def get_utm_epsg(lon: float, lat: float) -> int:
        """
        Calculates WGS84 UTM Zone EPSG code for a given longitude and latitude.
        North hemisphere: EPSG:32601 - 32660
        South hemisphere: EPSG:32701 - 32760
        """
        # Clamp latitude to valid ranges
        lat = max(-80.0, min(84.0, lat))
        # Normalize longitude to [-180, 180]
        lon = (lon + 180.0) % 360.0 - 180.0
        
        zone = math.floor((lon + 180.0) / 6.0) + 1
        zone = max(1, min(60, zone))
        
        if lat >= 0:
            return 32600 + zone
        else:
            return 32700 + zone

    @classmethod
    def determine_optimal_projected_crs(cls, gdf: gpd.GeoDataFrame) -> str:
        """
        Selects an appropriate metric projected CRS for measurement.
        If current CRS is geographic (degrees), computes centroid and determines local UTM zone.
        If current CRS is already projected, validates it or falls back to UTM.
        """
        source_crs = gdf.crs
        
        # Check if CRS is missing or unparseable
        if source_crs is None:
            logger.warning("No CRS detected in dataset. Assuming EPSG:4326 geographic coordinates.")
            source_crs = CRS.from_epsg(4326)
            
        try:
            crs_obj = CRS.from_user_input(source_crs) if not isinstance(source_crs, CRS) else source_crs
        except Exception as e:
            logger.warning(f"Could not parse CRS '{source_crs}': {e}. Falling back to EPSG:4326.")
            crs_obj = CRS.from_epsg(4326)

        # If already a projected metric CRS, keep it or use local UTM
        if crs_obj.is_projected:
            epsg = crs_obj.to_epsg()
            if epsg:
                logger.info(f"Dataset already uses projected CRS: EPSG:{epsg}")
                return f"EPSG:{epsg}"
            
        # Determine centroid of valid non-empty geometries in geographic terms
        try:
            # Re-project bounding box/centroid to EPSG:4326 if needed
            if not crs_obj.is_geographic:
                transformer = Transformer.from_crs(crs_obj, CRS.from_epsg(4326), always_xy=True)
                # Reproject bounds
                minx, miny, maxx, maxy = gdf.total_bounds
                center_x, center_y = (minx + maxx) / 2.0, (miny + maxy) / 2.0
                center_x, center_y = transformer.transform(center_x, center_y)
            else:
                minx, miny, maxx, maxy = gdf.total_bounds
                center_x, center_y = (minx + maxx) / 2.0, (miny + maxy) / 2.0
                
            epsg_code = cls.get_utm_epsg(center_x, center_y)
            projected_crs_str = f"EPSG:{epsg_code}"
            logger.info(f"Determined optimal local UTM projected CRS: {projected_crs_str} for center ({center_x:.4f}, {center_y:.4f})")
            return projected_crs_str
        except Exception as e:
            logger.error(f"Error determining UTM zone: {e}. Defaulting to EPSG:3857 (Web Mercator).")
            return "EPSG:3857"

    @staticmethod
    def transform_geometry(geometry: base.BaseGeometry, source_crs: str, target_crs: str) -> base.BaseGeometry:
        """
        Reprojects a single Shapely geometry from source_crs to target_crs.
        """
        if source_crs == target_crs:
            return geometry
            
        try:
            src = CRS.from_user_input(source_crs)
            tgt = CRS.from_user_input(target_crs)
            transformer = Transformer.from_crs(src, tgt, always_xy=True)
            return transform(transformer.transform, geometry)
        except Exception as e:
            logger.error(f"Failed to transform geometry from {source_crs} to {target_crs}: {e}")
            raise ValueError(f"Geometry transformation error: {e}")
