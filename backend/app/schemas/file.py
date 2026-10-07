from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.file_record import ProcessingStatus

class FileBase(BaseModel):
    filename: str
    file_type: str

class FileUploadResponse(BaseModel):
    id: str
    filename: str
    feature_count: int
    crs: str
    projected_crs: Optional[str] = None
    status: ProcessingStatus
    message: str = "File uploaded and processed successfully"

class FileInfoResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    feature_count: int
    crs: Optional[str] = "EPSG:4326"
    projected_crs: Optional[str] = None
    status: ProcessingStatus
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class FileListItem(BaseModel):
    id: str
    filename: str
    file_type: str
    feature_count: int
    crs: Optional[str] = "EPSG:4326"
    projected_crs: Optional[str] = None
    status: ProcessingStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
