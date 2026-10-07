from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.file_record import FileRecord, ProcessingStatus
from app.models.feature_record import FeatureRecord
from app.schemas.file import FileUploadResponse, FileInfoResponse, FileListItem
from app.services.file_storage import FileStorageService
from app.services.file_processor import FileProcessor

router = APIRouter(prefix="/files", tags=["Files"])

@router.post(
    "/",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a geospatial file (.zip Shapefile or .kml)",
    description="Accepts a .zip file containing a Shapefile (.shp, .shx, .dbf) or a .kml file. Processes features and computes metric measurements."
)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # 1. Save uploaded file to disk
    file_id, file_ext, storage_path, file_size = FileStorageService.save_upload_file(file)

    # 2. Create initial database record
    file_record = FileRecord(
        id=file_id,
        filename=file.filename or f"uploaded{file_ext}",
        file_type=file_ext,
        file_size=file_size,
        storage_path=str(storage_path),
        status=ProcessingStatus.PENDING,
        feature_count=0
    )
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)

    # 3. Process the file
    processor = FileProcessor(db)
    processed_record = await processor.process_file(file_id)

    if processed_record.status == ProcessingStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process geospatial file: {processed_record.error_message}"
        )

    return FileUploadResponse(
        id=processed_record.id,
        filename=processed_record.filename,
        feature_count=processed_record.feature_count,
        crs=processed_record.crs or "EPSG:4326",
        projected_crs=processed_record.projected_crs,
        status=processed_record.status,
        message="File processed and measurements calculated successfully."
    )

@router.get(
    "/",
    response_model=List[FileListItem],
    summary="List all uploaded files"
)
async def list_files(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(FileRecord).order_by(FileRecord.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    files = result.scalars().all()
    return files

@router.get(
    "/{id}/",
    response_model=FileInfoResponse,
    summary="Get file information by ID"
)
async def get_file_info(
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

    return file_record

@router.delete(
    "/{id}/",
    status_code=status.HTTP_200_OK,
    summary="Delete file and associated features"
)
async def delete_file(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(FileRecord).where(FileRecord.id == id)
    result = await db.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{id}' not found."
        )

    # Delete physical file from disk
    FileStorageService.delete_stored_file(file_record.storage_path)

    # Delete database record
    await db.delete(file_record)
    await db.commit()

    return {"message": f"File '{id}' and all associated measurements deleted successfully."}
