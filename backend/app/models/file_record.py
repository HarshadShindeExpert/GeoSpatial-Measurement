import enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Integer, Float, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

def utc_now():
    return datetime.now(timezone.utc)

class FileRecord(Base):
    __tablename__ = "file_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    feature_count: Mapped[int] = mapped_column(Integer, default=0)
    crs: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default="EPSG:4326")
    projected_crs: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    # Relationships
    features: Mapped[List["FeatureRecord"]] = relationship(
        "FeatureRecord", back_populates="file", cascade="all, delete-orphan"
    )
