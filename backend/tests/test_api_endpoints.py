import pytest
from pathlib import Path
from httpx import AsyncClient

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_upload_kml_file(async_client: AsyncClient):
    kml_path = SAMPLE_DIR / "sample_polygons.kml"
    assert kml_path.exists(), "Sample KML file must exist"

    with open(kml_path, "rb") as f:
        response = await async_client.post(
            "/api/files/",
            files={"file": ("sample_polygons.kml", f, "application/vnd.google-earth.kml+xml")}
        )

    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data
    assert data["filename"] == "sample_polygons.kml"
    assert data["feature_count"] == 3
    assert data["status"] == "COMPLETED"
    
    file_id = data["id"]

    # Test GET /api/files/{id}/
    info_resp = await async_client.get(f"/api/files/{file_id}/")
    assert info_resp.status_code == 200
    info_data = info_resp.json()
    assert info_data["id"] == file_id
    assert info_data["feature_count"] == 3

    # Test GET /api/files/{id}/measurements/
    meas_resp = await async_client.get(f"/api/files/{file_id}/measurements/")
    assert meas_resp.status_code == 200
    meas_data = meas_resp.json()
    assert meas_data["file_id"] == file_id
    assert meas_data["summary"]["total_features"] == 3
    assert meas_data["summary"]["polygon_count"] >= 1
    assert len(meas_data["features"]) == 3

    # Test GET /api/files/{id}/geojson/
    geo_resp = await async_client.get(f"/api/files/{file_id}/geojson/")
    assert geo_resp.status_code == 200
    geo_data = geo_resp.json()
    assert geo_data["type"] == "FeatureCollection"
    assert len(geo_data["features"]) == 3

@pytest.mark.asyncio
async def test_upload_shapefile_zip(async_client: AsyncClient):
    zip_path = SAMPLE_DIR / "sample_shapefile.zip"
    assert zip_path.exists(), "Sample shapefile zip must exist"

    with open(zip_path, "rb") as f:
        response = await async_client.post(
            "/api/files/",
            files={"file": ("sample_shapefile.zip", f, "application/zip")}
        )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["filename"] == "sample_shapefile.zip"
    assert data["feature_count"] == 3
    assert data["status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_upload_invalid_file_type(async_client: AsyncClient):
    response = await async_client.post(
        "/api/files/",
        files={"file": ("test.txt", b"dummy content", "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_nonexistent_file(async_client: AsyncClient):
    response = await async_client.get("/api/files/nonexistent_123/")
    assert response.status_code == 404
