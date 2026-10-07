import pytest
import io
import zipfile
from pathlib import Path
from httpx import AsyncClient
from app.security import SecurityValidator, SecurityValidationError, InputSanitizer

def test_xss_input_sanitizer():
    unsafe_text = "<script>alert('xss')</script>"
    clean_text = InputSanitizer.sanitize_string(unsafe_text)
    assert "<script>" not in clean_text
    assert "&lt;script&gt;" in clean_text

    unsafe_dict = {
        "name": "<b onmouseover=alert(1)>Parcel A</b>",
        "link": "javascript:alert(1)"
    }
    clean_dict = InputSanitizer.sanitize_dict(unsafe_dict)
    assert "javascript:" not in clean_dict["link"]
    assert "&lt;b" in clean_dict["name"]

def test_zip_slip_prevention(tmp_path):
    zip_path = tmp_path / "zip_slip.zip"
    target_extract_dir = tmp_path / "extracted"
    target_extract_dir.mkdir()

    # Create malicious zip containing path traversal filename ../../../malicious.txt
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("../../../malicious.txt", "evil payload")

    with pytest.raises(SecurityValidationError) as excinfo:
        SecurityValidator.safe_extract_zip(zip_path, target_extract_dir)

    assert "Zip Slip path traversal attempt" in str(excinfo.value)

@pytest.mark.asyncio
async def test_spoof_magic_bytes_rejection(async_client: AsyncClient):
    # Fake ZIP file containing plain text instead of PK magic bytes
    fake_zip_bytes = b"THIS IS NOT A REAL ZIP FILE HEADER"

    response = await async_client.post(
        "/api/files/",
        files={"file": ("fake_shapefile.zip", fake_zip_bytes, "application/zip")}
    )

    assert response.status_code == 400
    assert "lacks valid ZIP header magic bytes" in response.json()["detail"]

@pytest.mark.asyncio
async def test_security_headers(async_client: AsyncClient):
    response = await async_client.get("/api/health")
    assert response.status_code == 200

    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Content-Security-Policy" in headers
