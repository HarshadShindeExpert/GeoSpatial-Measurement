from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.schemas.measurement import AreaMeasurement, LengthMeasurement, GeodesicMeasurement
from app.models.feature_record import MeasurementStatus

class FeatureDetailResponse(BaseModel):
    id: int
    file_id: str
    feature_index: int
    feature_id_attr: Optional[str] = None
    geometry_type: str
    geometry: Dict[str, Any]
    crs: str
    properties: Dict[str, Any]
    measurement_status: MeasurementStatus
    area: Optional[AreaMeasurement] = None
    length: Optional[LengthMeasurement] = None
    geodesic: Optional[GeodesicMeasurement] = None
    notes: Optional[str] = None

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]

class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    crs: Optional[Dict[str, Any]] = None
    features: list[GeoJSONFeature]
