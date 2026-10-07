import httpx
from pathlib import Path

BASE_URL = "http://127.0.0.1:8008"
SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data"

def test_live_server():
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Health check
        res_health = client.get("/api/health")
        assert res_health.status_code == 200, res_health.text
        print("[PASS] Live GET /api/health passed:", res_health.json())

        # 2. Upload KML
        kml_path = SAMPLE_DIR / "sample_polygons.kml"
        with open(kml_path, "rb") as f:
            res_kml = client.post("/api/files/", files={"file": ("sample_polygons.kml", f, "application/vnd.google-earth.kml+xml")})
        assert res_kml.status_code == 201, res_kml.text
        kml_data = res_kml.json()
        print("[PASS] Live POST /api/files/ (KML) passed:", kml_data)
        kml_id = kml_data["id"]

        # 3. Upload Shapefile Zip
        zip_path = SAMPLE_DIR / "sample_shapefile.zip"
        with open(zip_path, "rb") as f:
            res_zip = client.post("/api/files/", files={"file": ("sample_shapefile.zip", f, "application/zip")})
        assert res_zip.status_code == 201, res_zip.text
        zip_data = res_zip.json()
        print("[PASS] Live POST /api/files/ (Shapefile Zip) passed:", zip_data)
        zip_id = zip_data["id"]

        # 4. List Files
        res_list = client.get("/api/files/")
        assert res_list.status_code == 200
        print(f"[PASS] Live GET /api/files/ passed ({len(res_list.json())} files returned)")

        # 5. Get File Info
        res_info = client.get(f"/api/files/{kml_id}/")
        assert res_info.status_code == 200
        print("[PASS] Live GET /api/files/{{id}}/ passed:", res_info.json())

        # 6. Get Measurements
        res_meas = client.get(f"/api/files/{kml_id}/measurements/")
        assert res_meas.status_code == 200
        meas_json = res_meas.json()
        assert meas_json["summary"]["total_features"] > 0
        print("[PASS] Live GET /api/files/{{id}}/measurements/ passed:", meas_json["summary"])

        # 7. Get GeoJSON
        res_geo = client.get(f"/api/files/{kml_id}/geojson/")
        assert res_geo.status_code == 200
        print(f"[PASS] Live GET /api/files/{{id}}/geojson/ passed ({len(res_geo.json()['features'])} GeoJSON features)")

        # 8. Delete File
        res_del = client.delete(f"/api/files/{kml_id}/")
        assert res_del.status_code == 200
        print("[PASS] Live DELETE /api/files/{{id}}/ passed")

if __name__ == "__main__":
    test_live_server()
