from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from app.models.feature_record import MeasurementStatus

class AreaMeasurement(BaseModel):
    sq_meters: float
    hectares: float
    sq_km: float

class LengthMeasurement(BaseModel):
    meters: float
    kilometers: float

class GeodesicMeasurement(BaseModel):
    geodesic_area_sq_m: Optional[float] = None
    geodesic_length_m: Optional[float] = None

class FeatureMeasurement(BaseModel):
    feature_index: int
    feature_id: Optional[str] = None
    geometry_type: str
    crs: str
    measurement_status: MeasurementStatus
    area: Optional[AreaMeasurement] = None
    length: Optional[LengthMeasurement] = None
    geodesic: Optional[GeodesicMeasurement] = None
    properties: Dict[str, Any] = {}
    notes: Optional[str] = None

class MeasurementSummary(BaseModel):
    total_features: int
    polygon_count: int
    linestring_count: int
    point_count: int
    other_count: int
    total_area_sq_m: float
    total_area_hectares: float
    total_area_sq_km: float
    total_length_m: float
    total_length_km: float

class FileMeasurementsResponse(BaseModel):
    file_id: str
    filename: str
    crs: str
    projected_crs: str
    summary: MeasurementSummary
    features: List[FeatureMeasurement]
