import os
import zipfile
from pathlib import Path
from fastapi import HTTPException, status
import defusedxml.ElementTree as SafeET

class SecurityValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class SecurityValidator:
    ZIP_MAGIC_BYTES = [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08']
    
    @classmethod
    def validate_file_magic_bytes(cls, file_path: Path, file_ext: str):
        """
        Inspects raw file header bytes to verify actual content matches file extension.
        Prevents MIME-spoofing and executable uploads disguised as .kml or .zip.
        """
        if not file_path.exists():
            raise SecurityValidationError("File not found on server.")

        with open(file_path, "rb") as f:
            header = f.read(512)

        if file_ext == ".zip":
            if not any(header.startswith(magic) for magic in cls.ZIP_MAGIC_BYTES):
                raise SecurityValidationError("Security Check Failed: Uploaded file claims to be a .zip archive but lacks valid ZIP header magic bytes.")
        
        elif file_ext == ".kml":
            # Must be valid text containing xml or kml tag
            content_str = header.decode("utf-8", errors="ignore").strip().lower()
            if not ("<?xml" in content_str or "<kml" in content_str or "<document" in content_str or "<placemark" in content_str):
                raise SecurityValidationError("Security Check Failed: Uploaded file claims to be a .kml file but lacks valid XML/KML content.")

    @classmethod
    def safe_extract_zip(cls, zip_path: Path, target_dir: Path):
        """
        Extracts ZIP archive while guarding against 'Zip Slip' path traversal attacks.
        Ensures extracted files remain inside target_dir.
        """
        target_dir_resolved = target_dir.resolve()

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.infolist():
                # Resolve destination path
                member_path = (target_dir / member.filename).resolve()
                
                # Verify resolved path is strictly relative to target_dir
                try:
                    member_path.relative_to(target_dir_resolved)
                except ValueError:
                    raise SecurityValidationError(f"Security Warning: Zip Slip path traversal attempt detected in member '{member.filename}'. Extraction aborted.")

            # Safe to extract
            zip_ref.extractall(target_dir)

    @classmethod
    def safe_parse_kml_xml(cls, kml_path: Path):
        """
        Parses KML file using defusedxml to prevent XML External Entity (XXE) and XML Entity Expansion attacks.
        """
        try:
            tree = SafeET.parse(kml_path)
            return tree.getroot()
        except Exception as e:
            raise SecurityValidationError(f"Invalid or unsafe XML structure in KML file: {str(e)}")
