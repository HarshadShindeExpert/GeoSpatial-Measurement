import os
import uuid
import shutil
import logging
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from app.config import settings

logger = logging.getLogger("geospatial.storage")

class FileStorageService:
    @staticmethod
    def save_upload_file(upload_file: UploadFile) -> tuple[str, str, Path, int]:
        """
        Validates uploaded file extension, size, and saves to storage directory.
        Returns: (file_id, file_type, file_path, file_size)
        """
        filename = upload_file.filename or "uploaded_file"
        file_ext = Path(filename).suffix.lower()

        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        file_id = uuid.uuid4().hex[:12]
        saved_filename = f"{file_id}_{filename}"
        target_path = settings.UPLOAD_DIR / saved_filename

        try:
            file_size = 0
            with open(target_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
            
            file_size = target_path.stat().st_size

            # Check max size limit
            max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
            if file_size > max_bytes:
                target_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds maximum allowed limit of {settings.MAX_FILE_SIZE_MB}MB."
                )

            logger.info(f"File {filename} saved successfully as {saved_filename} ({file_size} bytes).")
            return file_id, file_ext, target_path, file_size

        except Exception as e:
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            if isinstance(e, HTTPException):
                raise e
            logger.error(f"Error saving upload file {filename}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save uploaded file: {str(e)}"
            )

    @staticmethod
    def delete_stored_file(file_path_str: str):
        path = Path(file_path_str)
        if path.exists():
            try:
                path.unlink()
                logger.info(f"Deleted file {path}")
            except Exception as e:
                logger.warning(f"Failed to delete stored file {path}: {e}")
