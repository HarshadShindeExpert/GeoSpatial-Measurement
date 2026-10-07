import logging
from typing import Dict, Any, Optional, Tuple
from shapely.geometry import base, shape, Polygon, MultiPolygon, LineString, MultiLineString, Point, MultiPoint, GeometryCollection
from shapely.validation import make_valid
from pyproj import Geod
from app.models.feature_record import MeasurementStatus
from app.services.crs_service import CRSService

logger = logging.getLogger("geospatial.measurement")

class MeasurementService:
    def __init__(self):
        self.geod = Geod(ellps="WGS84")

    def process_feature_measurement(
        self,
        geometry: base.BaseGeometry,
        source_crs: str,
        projected_crs: str
    ) -> Dict[str, Any]:
        """
        Calculates planar (projected metric) and geodesic measurements for a Shapely geometry.
        Returns a dict containing measurement values, status, and any repair notes.
        """
        result = {
            "measurement_status": MeasurementStatus.NOT_APPLICABLE,
            "area_sq_m": None,
            "area_hectares": None,
            "area_sq_km": None,
            "length_m": None,
            "length_km": None,
            "geodesic_area_sq_m": None,
            "geodesic_length_m": None,
            "notes": None
        }

        if geometry is None or geometry.is_empty:
            result["measurement_status"] = MeasurementStatus.INVALID_GEOMETRY
            result["notes"] = "Geometry is empty or null"
            return result

        # Check and repair geometry if invalid
        working_geom = geometry
        notes_list = []
        
        if not working_geom.is_valid:
            try:
                working_geom = make_valid(working_geom)
                notes_list.append("Geometry was invalid and was automatically repaired using shapely.validation.make_valid.")
            except Exception as e:
                logger.warning(f"Failed to repair invalid geometry: {e}")
                result["measurement_status"] = MeasurementStatus.INVALID_GEOMETRY
                result["notes"] = f"Invalid geometry could not be repaired: {str(e)}"
                return result

        # Re-project working geometry to projected metric CRS
        try:
            projected_geom = CRSService.transform_geometry(working_geom, source_crs, projected_crs)
        except Exception as e:
            logger.error(f"Failed to reproject geometry to {projected_crs}: {e}")
            result["measurement_status"] = MeasurementStatus.UNSUPPORTED
            result["notes"] = f"Reprojection error: {str(e)}"
            return result

        # Also get WGS84 geometry for geodesic math
        wgs84_geom = None
        if source_crs != "EPSG:4326":
            try:
                wgs84_geom = CRSService.transform_geometry(working_geom, source_crs, "EPSG:4326")
            except Exception:
                wgs84_geom = None
        else:
            wgs84_geom = working_geom

        geom_type = projected_geom.geom_type

        try:
            if geom_type in ["Polygon", "MultiPolygon"]:
                area_m2 = abs(float(projected_geom.area))
                result["area_sq_m"] = round(area_m2, 4)
                result["area_hectares"] = round(area_m2 / 10000.0, 6)
                result["area_sq_km"] = round(area_m2 / 1000000.0, 6)
                
                # Also include boundary perimeter as length
                perimeter_m = float(projected_geom.length)
                result["length_m"] = round(perimeter_m, 4)
                result["length_km"] = round(perimeter_m / 1000.0, 6)
                
                result["measurement_status"] = MeasurementStatus.CALCULATED

                # Geodesic Area
                if wgs84_geom is not None:
                    try:
                        g_area, g_perim = self.geod.geometry_area_perimeter(wgs84_geom)
                        result["geodesic_area_sq_m"] = round(abs(float(g_area)), 4)
                        result["geodesic_length_m"] = round(abs(float(g_perim)), 4)
                    except Exception as geod_err:
                        logger.warning(f"Geodesic area calculation failed: {geod_err}")

            elif geom_type in ["LineString", "MultiLineString"]:
                length_m = float(projected_geom.length)
                result["length_m"] = round(length_m, 4)
                result["length_km"] = round(length_m / 1000.0, 6)
                result["area_sq_m"] = 0.0
                result["area_hectares"] = 0.0
                result["area_sq_km"] = 0.0
                result["measurement_status"] = MeasurementStatus.CALCULATED

                # Geodesic Length
                if wgs84_geom is not None:
                    try:
                        g_len = self.geod.geometry_length(wgs84_geom)
                        result["geodesic_length_m"] = round(abs(float(g_len)), 4)
                    except Exception as geod_err:
                        logger.warning(f"Geodesic length calculation failed: {geod_err}")

            elif geom_type in ["Point", "MultiPoint"]:
                result["measurement_status"] = MeasurementStatus.NOT_APPLICABLE
                result["notes"] = "Point geometries do not have area or length measurements."

            elif geom_type == "GeometryCollection":
                total_area = 0.0
                total_length = 0.0
                for sub_g in projected_geom.geoms:
                    if sub_g.geom_type in ["Polygon", "MultiPolygon"]:
                        total_area += sub_g.area
                    elif sub_g.geom_type in ["LineString", "MultiLineString"]:
                        total_length += sub_g.length
                
                result["area_sq_m"] = round(total_area, 4)
                result["area_hectares"] = round(total_area / 10000.0, 6)
                result["area_sq_km"] = round(total_area / 1000000.0, 6)
                result["length_m"] = round(total_length, 4)
                result["length_km"] = round(total_length / 1000.0, 6)
                result["measurement_status"] = MeasurementStatus.CALCULATED
                notes_list.append("GeometryCollection components were aggregated.")

            else:
                result["measurement_status"] = MeasurementStatus.UNSUPPORTED
                result["notes"] = f"Geometry type '{geom_type}' is not supported for automatic measurement."

        except Exception as err:
            logger.error(f"Error calculating measurement for {geom_type}: {err}", exc_info=True)
            result["measurement_status"] = MeasurementStatus.UNSUPPORTED
            result["notes"] = f"Measurement computation error: {str(err)}"

        if notes_list:
            existing = result.get("notes")
            result["notes"] = (existing + " " if existing else "") + " ".join(notes_list)

        return result
