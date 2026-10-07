import pytest
import io
import zipfile
from pathlib import Path
from httpx import AsyncClient
from shapely.geometry import MultiPolygon, Polygon, MultiLineString, LineString, Point, GeometryCollection
from app.services.measurement_service import MeasurementService
from app.models.feature_record import MeasurementStatus

@pytest.fixture
def measurement_service():
    return MeasurementService()

def test_multipolygon_measurement(measurement_service):
    poly1 = Polygon([(77.10, 28.55), (77.11, 28.55), (77.11, 28.56), (77.10, 28.56), (77.10, 28.55)])
    poly2 = Polygon([(77.12, 28.57), (77.13, 28.57), (77.13, 28.58), (77.12, 28.58), (77.12, 28.57)])
    multipoly = MultiPolygon([poly1, poly2])

    res = measurement_service.process_feature_measurement(
        geometry=multipoly,
        source_crs="EPSG:4326",
        projected_crs="EPSG:32643"
    )

    assert res["measurement_status"] == MeasurementStatus.CALCULATED
    assert res["area_sq_m"] > 0
    assert res["area_hectares"] > 0
    assert res["length_m"] > 0

def test_multilinestring_measurement(measurement_service):
    line1 = LineString([(77.10, 28.55), (77.11, 28.56)])
    line2 = LineString([(77.12, 28.57), (77.13, 28.58)])
    multiline = MultiLineString([line1, line2])

    res = measurement_service.process_feature_measurement(
        geometry=multiline,
        source_crs="EPSG:4326",
        projected_crs="EPSG:32643"
    )

    assert res["measurement_status"] == MeasurementStatus.CALCULATED
    assert res["length_m"] > 0
    assert res["length_km"] > 0

def test_geometry_collection_measurement(measurement_service):
    poly = Polygon([(77.10, 28.55), (77.11, 28.55), (77.11, 28.56), (77.10, 28.56), (77.10, 28.55)])
    line = LineString([(77.10, 28.55), (77.15, 28.60)])
    coll = GeometryCollection([poly, line])

    res = measurement_service.process_feature_measurement(
        geometry=coll,
        source_crs="EPSG:4326",
        projected_crs="EPSG:32643"
    )

    assert res["measurement_status"] == MeasurementStatus.CALCULATED
    assert res["area_sq_m"] > 0
    assert res["length_m"] > 0

@pytest.mark.asyncio
async def test_upload_corrupt_zip(async_client: AsyncClient):
    # Upload zip containing invalid text file instead of .shp
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        zf.writestr("read_me.txt", "This is not a shapefile")
    zip_buffer.seek(0)

    response = await async_client.post(
        "/api/files/",
        files={"file": ("corrupt.zip", zip_buffer, "application/zip")}
    )

    assert response.status_code == 422
    assert "Zip file does not contain any .shp" in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_empty_kml(async_client: AsyncClient):
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
      <Document>
        <name>Empty KML</name>
      </Document>
    </kml>"""

    response = await async_client.post(
        "/api/files/",
        files={"file": ("empty.kml", kml_content.encode("utf-8"), "application/vnd.google-earth.kml+xml")}
    )

    assert response.status_code == 422
    assert "No Placemarks found in KML file" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_file_endpoint(async_client: AsyncClient):
    SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"
    kml_path = SAMPLE_DIR / "sample_polygons.kml"

    with open(kml_path, "rb") as f:
        upload_resp = await async_client.post(
            "/api/files/",
            files={"file": ("to_delete.kml", f, "application/vnd.google-earth.kml+xml")}
        )

    file_id = upload_resp.json()["id"]

    # Verify file exists
    info_resp = await async_client.get(f"/api/files/{file_id}/")
    assert info_resp.status_code == 200

    # Delete file
    del_resp = await async_client.delete(f"/api/files/{file_id}/")
    assert del_resp.status_code == 200

    # Verify 404 on GET
    info_resp2 = await async_client.get(f"/api/files/{file_id}/")
    assert info_resp2.status_code == 404
