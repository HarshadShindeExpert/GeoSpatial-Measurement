import os
import tempfile
import json
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import shape, mapping, Polygon, LineString, Point
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.file_record import FileRecord, ProcessingStatus
from app.models.feature_record import FeatureRecord, MeasurementStatus
from app.services.crs_service import CRSService
from app.services.measurement_service import MeasurementService
from app.security import SecurityValidator, InputSanitizer
from app.config import settings

logger = logging.getLogger("geospatial.processor")

def sanitize_properties(props: dict) -> dict:
    """
    Sanitizes dictionary properties for JSON serialization and XSS security.
    """
    sanitized = {}
    for k, v in props.items():
        if isinstance(v, (np.integer, int)):
            sanitized[k] = int(v)
        elif isinstance(v, (np.floating, float)):
            sanitized[k] = None if np.isnan(v) else float(v)
        elif isinstance(v, (np.ndarray, list)):
            sanitized[k] = [int(x) if isinstance(x, np.integer) else float(x) if isinstance(x, np.floating) else str(x) for x in v]
        elif pd.isna(v):
            sanitized[k] = None
        elif isinstance(v, (bytes, bytearray)):
            sanitized[k] = v.decode("utf-8", errors="ignore")
        else:
            sanitized[k] = str(v)
            
    # Apply XSS InputSanitizer to neutralize executable HTML/JS payloads
    return InputSanitizer.sanitize_dict(sanitized)

class FileProcessor:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.measurement_service = MeasurementService()

    async def process_file(self, file_record_id: str) -> FileRecord:
        """
        Loads the file record, reads the geospatial file, extracts features and measurements,
        and saves records into the database.
        """
        stmt = select(FileRecord).where(FileRecord.id == file_record_id)
        result = await self.db.execute(stmt)
        file_record = result.scalar_one_or_none()

        if not file_record:
            raise ValueError(f"File record {file_record_id} not found.")

        file_record.status = ProcessingStatus.PROCESSING
        await self.db.commit()

        file_path = Path(file_record.storage_path)

        try:
            gdf = self._load_geodataframe(file_path, file_record.file_type)

            if gdf is None or gdf.empty:
                raise ValueError("No valid features or geometries found in file.")

            # Detect source CRS
            source_crs_str = self._detect_source_crs(gdf)
            file_record.crs = source_crs_str

            # Determine optimal projected CRS (e.g. local UTM zone)
            projected_crs_str = CRSService.determine_optimal_projected_crs(gdf)
            file_record.projected_crs = projected_crs_str

            feature_records = []
            feature_count = len(gdf)

            for idx, row in gdf.iterrows():
                geom = row.geometry
                
                # Extract properties (exclude geometry column)
                props_dict = row.drop(labels=['geometry']).to_dict() if 'geometry' in row else {}
                sanitized_props = sanitize_properties(props_dict)

                feat_id_attr = str(
                    sanitized_props.get("id") or 
                    sanitized_props.get("ID") or 
                    sanitized_props.get("Name") or 
                    sanitized_props.get("fid") or 
                    f"feature_{idx}"
                )

                if geom is None or geom.is_empty:
                    feat_record = FeatureRecord(
                        file_id=file_record.id,
                        feature_index=int(idx),
                        feature_id_attr=feat_id_attr,
                        geometry_type="Unknown",
                        geometry_geojson_str=json.dumps({}),
                        crs=source_crs_str,
                        properties_json_str=json.dumps(sanitized_props),
                        measurement_status=MeasurementStatus.INVALID_GEOMETRY,
                        notes="Empty or null geometry"
                    )
                else:
                    geom_type = geom.geom_type
                    geom_geojson = mapping(geom)

                    # Calculate measurements
                    meas = self.measurement_service.process_feature_measurement(
                        geometry=geom,
                        source_crs=source_crs_str,
                        projected_crs=projected_crs_str
                    )

                    feat_record = FeatureRecord(
                        file_id=file_record.id,
                        feature_index=int(idx),
                        feature_id_attr=feat_id_attr,
                        geometry_type=geom_type,
                        geometry_geojson_str=json.dumps(geom_geojson),
                        crs=source_crs_str,
                        properties_json_str=json.dumps(sanitized_props),
                        area_sq_m=meas["area_sq_m"],
                        area_hectares=meas["area_hectares"],
                        area_sq_km=meas["area_sq_km"],
                        length_m=meas["length_m"],
                        length_km=meas["length_km"],
                        geodesic_area_sq_m=meas["geodesic_area_sq_m"],
                        geodesic_length_m=meas["geodesic_length_m"],
                        measurement_status=meas["measurement_status"],
                        notes=meas["notes"]
                    )
                feature_records.append(feat_record)

            file_record.feature_count = feature_count
            file_record.status = ProcessingStatus.COMPLETED
            file_record.error_message = None

            self.db.add_all(feature_records)
            await self.db.commit()
            await self.db.refresh(file_record)
            logger.info(f"File {file_record_id} successfully processed with {feature_count} features.")
            return file_record

        except Exception as e:
            logger.error(f"Failed to process file {file_record_id}: {e}", exc_info=True)
            file_record.status = ProcessingStatus.FAILED
            file_record.error_message = str(e)
            await self.db.commit()
            await self.db.refresh(file_record)
            return file_record

    def _load_geodataframe(self, file_path: Path, file_type: str) -> gpd.GeoDataFrame:
        """
        Loads Shapefiles (.zip) or KML (.kml) into a GeoPandas GeoDataFrame with Security Guards.
        """
        file_ext = file_path.suffix.lower()

        if file_ext == ".zip" or file_type == ".zip":
            return self._read_shapefile_zip(file_path)
        elif file_ext in [".kml", ".kmz"] or file_type == ".kml":
            return self._read_kml(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    def _read_shapefile_zip(self, zip_path: Path) -> gpd.GeoDataFrame:
        """
        Safely extracts zip file with Zip-Slip path traversal protection and reads Shapefile.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Security Check: Zip-Slip path traversal protection
            SecurityValidator.safe_extract_zip(zip_path, tmp_path)

            shp_files = list(tmp_path.rglob("*.shp"))
            if not shp_files:
                raise ValueError("Zip file does not contain any .shp (Shapefile) file.")

            main_shp = shp_files[0]
            logger.info(f"Reading shapefile: {main_shp}")
            gdf = gpd.read_file(main_shp)
            return gdf

    def _read_kml(self, kml_path: Path) -> gpd.GeoDataFrame:
        """
        Reads KML file using GeoPandas or safe defusedxml parser.
        """
        try:
            import fiona
            if hasattr(fiona, 'drvsupport') and hasattr(fiona.drvsupport, 'supported_drivers'):
                fiona.drvsupport.supported_drivers['KML'] = 'rw'
                fiona.drvsupport.supported_drivers['LIBKML'] = 'rw'
            gdf = gpd.read_file(kml_path, driver='KML')
            if gdf is not None and not gdf.empty:
                return gdf
        except Exception as err:
            logger.info(f"GeoPandas/Fiona direct KML read note: {err}. Using safe defusedxml parser.")

        return self._parse_kml_xml(kml_path)

    def _parse_kml_xml(self, kml_path: Path) -> gpd.GeoDataFrame:
        """
        Safe XML parser for KML Placemarks protecting against XXE attacks via defusedxml.
        """
        root = SecurityValidator.safe_parse_kml_xml(kml_path)

        def find_elem(element, tag):
            for child in element.iter():
                child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if child_tag.lower() == tag.lower():
                    return child
            return None

        def find_all_elems(element, tag):
            results = []
            for child in element.iter():
                child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if child_tag.lower() == tag.lower():
                    results.append(child)
            return results

        placemarks = find_all_elems(root, 'Placemark')
        if not placemarks:
            raise ValueError("No Placemarks found in KML file.")

        features = []
        for p_idx, p in enumerate(placemarks):
            name_elem = find_elem(p, 'name')
            desc_elem = find_elem(p, 'description')
            
            name = name_elem.text if (name_elem is not None and name_elem.text) else f"Placemark {p_idx+1}"
            description = desc_elem.text if (desc_elem is not None and desc_elem.text) else ""

            # Sanitize XSS strings
            clean_name = InputSanitizer.sanitize_string(name)
            clean_desc = InputSanitizer.sanitize_string(description)

            poly_elem = find_elem(p, 'Polygon')
            linestring_elem = find_elem(p, 'LineString')
            point_elem = find_elem(p, 'Point')

            geom = None

            if poly_elem is not None:
                coords_elem = find_elem(poly_elem, 'coordinates')
                if coords_elem is not None and coords_elem.text:
                    raw_coords = coords_elem.text.strip().split()
                    pts = []
                    for c in raw_coords:
                        parts = c.split(',')
                        if len(parts) >= 2:
                            pts.append((float(parts[0]), float(parts[1])))
                    if len(pts) >= 3:
                        geom = Polygon(pts)

            elif linestring_elem is not None:
                coords_elem = find_elem(linestring_elem, 'coordinates')
                if coords_elem is not None and coords_elem.text:
                    raw_coords = coords_elem.text.strip().split()
                    pts = []
                    for c in raw_coords:
                        parts = c.split(',')
                        if len(parts) >= 2:
                            pts.append((float(parts[0]), float(parts[1])))
                    if len(pts) >= 2:
                        geom = LineString(pts)

            elif point_elem is not None:
                coords_elem = find_elem(point_elem, 'coordinates')
                if coords_elem is not None and coords_elem.text:
                    parts = coords_elem.text.strip().split(',')
                    if len(parts) >= 2:
                        geom = Point(float(parts[0]), float(parts[1]))

            if geom is not None:
                features.append({
                    "Name": clean_name,
                    "Description": clean_desc,
                    "geometry": geom
                })

        if not features:
            raise ValueError("No Placemarks with valid coordinates found in KML.")

        gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")
        return gdf

    def _detect_source_crs(self, gdf: gpd.GeoDataFrame) -> str:
        if gdf.crs is None:
            return "EPSG:4326"
        epsg = gdf.crs.to_epsg()
        if epsg:
            return f"EPSG:{epsg}"
        return str(gdf.crs)
