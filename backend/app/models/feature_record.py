import enum
from typing import Optional
import json
from sqlalchemy import String, Integer, Float, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class MeasurementStatus(str, enum.Enum):
    CALCULATED = "CALCULATED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INVALID_GEOMETRY = "INVALID_GEOMETRY"
    UNSUPPORTED = "UNSUPPORTED"

class FeatureRecord(Base):
    __tablename__ = "feature_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(String(36), ForeignKey("file_records.id", ondelete="CASCADE"), nullable=False)
    feature_index: Mapped[int] = mapped_column(Integer, nullable=False)
    feature_id_attr: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    geometry_type: Mapped[str] = mapped_column(String(50), nullable=False)
    geometry_geojson_str: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    crs: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="EPSG:4326")
    properties_json_str: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    
    # Measurements
    area_sq_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    area_hectares: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    area_sq_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    length_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    length_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    geodesic_area_sq_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    geodesic_length_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    measurement_status: Mapped[MeasurementStatus] = mapped_column(
        Enum(MeasurementStatus), default=MeasurementStatus.NOT_APPLICABLE, nullable=False
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationship
    file: Mapped["FileRecord"] = relationship("FileRecord", back_populates="features")

    @property
    def geometry(self) -> dict:
        return json.loads(self.geometry_geojson_str) if self.geometry_geojson_str else {}

    @property
    def properties(self) -> dict:
        return json.loads(self.properties_json_str) if self.properties_json_str else {}
