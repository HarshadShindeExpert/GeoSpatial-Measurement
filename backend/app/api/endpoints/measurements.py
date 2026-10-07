from typing import List, Dict, Any
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.file_record import FileRecord, ProcessingStatus
from app.models.feature_record import FeatureRecord, MeasurementStatus
from app.schemas.measurement import (
    FileMeasurementsResponse,
    FeatureMeasurement,
    MeasurementSummary,
    AreaMeasurement,
    LengthMeasurement,
    GeodesicMeasurement
)
from app.schemas.feature import GeoJSONFeatureCollection, GeoJSONFeature

router = APIRouter(prefix="/files", tags=["Measurements"])

@router.get(
    "/{id}/measurements/",
    response_model=FileMeasurementsResponse,
    summary="Get measurements for features in an uploaded file"
)
async def get_file_measurements(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    # Fetch file record
    stmt = select(FileRecord).where(FileRecord.id == id)
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{id}' was not found."
        )

    if file_record.status == ProcessingStatus.PENDING or file_record.status == ProcessingStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File is still processing. Please try again shortly."
        )

    if file_record.status == ProcessingStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File processing failed: {file_record.error_message}"
        )

    # Fetch features
    stmt_feat = select(FeatureRecord).where(FeatureRecord.file_id == id).order_by(FeatureRecord.feature_index)
    res_feat = await db.execute(stmt_feat)
    features = res_feat.scalars().all()

    feature_measurements: List[FeatureMeasurement] = []
    
    total_area_m2 = 0.0
    total_length_m = 0.0
    poly_count = 0
    line_count = 0
    point_count = 0
    other_count = 0

    for f in features:
        geom_type = f.geometry_type
        
        area_obj = None
        if f.area_sq_m is not None:
            area_obj = AreaMeasurement(
                sq_meters=f.area_sq_m,
                hectares=f.area_hectares or round(f.area_sq_m / 10000.0, 6),
                sq_km=f.area_sq_km or round(f.area_sq_m / 1000000.0, 6)
            )
            total_area_m2 += f.area_sq_m

        length_obj = None
        if f.length_m is not None:
            length_obj = LengthMeasurement(
                meters=f.length_m,
                kilometers=f.length_km or round(f.length_m / 1000.0, 6)
            )
            if geom_type in ["LineString", "MultiLineString"]:
                total_length_m += f.length_m

        geodesic_obj = None
        if f.geodesic_area_sq_m is not None or f.geodesic_length_m is not None:
            geodesic_obj = GeodesicMeasurement(
                geodesic_area_sq_m=f.geodesic_area_sq_m,
                geodesic_length_m=f.geodesic_length_m
            )

        if geom_type in ["Polygon", "MultiPolygon"]:
            poly_count += 1
        elif geom_type in ["LineString", "MultiLineString"]:
            line_count += 1
        elif geom_type in ["Point", "MultiPoint"]:
            point_count += 1
        else:
            other_count += 1

        feature_measurements.append(
            FeatureMeasurement(
                feature_index=f.feature_index,
                feature_id=f.feature_id_attr,
                geometry_type=geom_type,
                crs=f.crs or file_record.crs or "EPSG:4326",
                measurement_status=f.measurement_status,
                area=area_obj,
                length=length_obj,
                geodesic=geodesic_obj,
                properties=f.properties,
                notes=f.notes
            )
        )

    summary = MeasurementSummary(
        total_features=len(features),
        polygon_count=poly_count,
        linestring_count=line_count,
        point_count=point_count,
        other_count=other_count,
        total_area_sq_m=round(total_area_m2, 4),
        total_area_hectares=round(total_area_m2 / 10000.0, 6),
        total_area_sq_km=round(total_area_m2 / 1000000.0, 6),
        total_length_m=round(total_length_m, 4),
        total_length_km=round(total_length_m / 1000.0, 6)
    )

    return FileMeasurementsResponse(
        file_id=file_record.id,
        filename=file_record.filename,
        crs=file_record.crs or "EPSG:4326",
        projected_crs=file_record.projected_crs or "EPSG:3857",
        summary=summary,
        features=feature_measurements
    )

@router.get(
    "/{id}/geojson/",
    response_model=GeoJSONFeatureCollection,
    summary="Get GeoJSON FeatureCollection of uploaded file with measurement properties"
)
async def get_file_geojson(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(FileRecord).where(FileRecord.id == id)
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{id}' was not found."
        )

    stmt_feat = select(FeatureRecord).where(FeatureRecord.file_id == id).order_by(FeatureRecord.feature_index)
    res_feat = await db.execute(stmt_feat)
    features = res_feat.scalars().all()

    geojson_features = []
    for f in features:
        props = dict(f.properties)
        props["_measurement_status"] = f.measurement_status
        props["_area_sq_m"] = f.area_sq_m
        props["_area_hectares"] = f.area_hectares
        props["_length_m"] = f.length_m
        props["_length_km"] = f.length_km
        props["_geometry_type"] = f.geometry_type
        props["_feature_index"] = f.feature_index

        geojson_features.append(
            GeoJSONFeature(
                geometry=f.geometry,
                properties=props
            )
        )

    return GeoJSONFeatureCollection(
        crs={"type": "name", "properties": {"name": file_record.crs or "EPSG:4326"}},
        features=geojson_features
    )
