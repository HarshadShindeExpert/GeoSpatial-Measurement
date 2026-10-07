# Geospatial File Measurement API & Web Platform 🌍📏

> A production-grade REST API and Web GIS platform built with **FastAPI**, **GeoPandas**, **PyProj**, **Shapely**, **SQLAlchemy (Async)**, and **React (TypeScript + Leaflet)** for uploading, processing, and measuring geospatial datasets (`.zip` Shapefiles and `.kml` files).

---

## 🌟 Key Features

- **Multi-Format Ingestion**: Supports Shapefiles bundled in `.zip` archives (`.shp`, `.shx`, `.dbf`, `.prj`) and `.kml` Placemark files.
- **Automated Coordinate System Transformation (CRS)**:
  - Detects incoming geographic coordinate reference systems (e.g. `EPSG:4326` WGS84).
  - Dynamically calculates the optimal local **WGS84 UTM Zone** (`EPSG:326XX` / `EPSG:327XX`) based on feature centroids to avoid degree distortion.
  - Reprojects geometries into planar metric projections prior to area & length math.
- **Precision Measurements**:
  - **Polygons / MultiPolygons**: Area ($m^2$, Hectares, $km^2$) and Perimeter length ($m$).
  - **LineStrings / MultiLineStrings**: Total length ($m$, $km$).
  - **Points / MultiPoints**: Gracefully handled with metadata (`NOT_APPLICABLE`).
  - **Geodesic Verification**: Computes WGS84 ellipsoidal geodesic area and length via `pyproj.Geod` alongside projected planar metrics.
- **Fault-Tolerant File Engine**:
  - Auto-repairs self-intersecting or invalid geometries via `shapely.validation.make_valid`.
  - Non-blocking error handling for unsupported geometry types or corrupted rows without crashing API worker threads.
- **Interactive GIS Dashboard (React + TypeScript + Leaflet)**:
  - Drag-and-drop file uploader with status badges (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
  - Interactive Leaflet Vector Map rendering color-coded layers with popup measurement cards.
  - Export capabilities for measurement reports in **JSON** and **CSV** formats.
- **Interactive Swagger Documentation**: OpenAPI 3.0 auto-generated docs at `/api/docs`.
- **Fully Containerized & Tested**: Docker & Docker Compose configuration + 100% passing Pytest suite.

---

## 📐 CRS Strategy & Measurement Mathematics

### 1. The Geographic Coordinate Problem
Geographic coordinates (`EPSG:4326` / WGS84) express positions in angular degrees ($\text{Latitude}, \text{Longitude}$). Calculating Euclidean area ($\Delta x \times \Delta y$) directly on degree values produces severe scale distortion that varies with latitude.

### 2. Automatic Projected UTM Zone Calculation
To ensure real-world metric accuracy (meters, hectares, $km^2$), the service executes an automatic projection algorithm:
1. Calculates dataset centroid $(\bar{\lambda}, \bar{\phi})$ in degrees.
2. Determines the standard WGS84 Universal Transverse Mercator (UTM) Zone:
   $$\text{Zone Number} = \left\lfloor \frac{\bar{\lambda} + 180}{6} \right\rfloor + 1$$
3. Maps North/South hemisphere to official EPSG codes:
   - Northern Hemisphere ($\bar{\phi} \ge 0$): $\text{EPSG} = 32600 + \text{Zone}$
   - Southern Hemisphere ($\bar{\phi} < 0$): $\text{EPSG} = 32700 + \text{Zone}$
4. Transforms Shapely geometries to the local metric UTM projection using `pyproj.Transformer(always_xy=True)` before computing area and length.

### 3. Dual Geodesic Verification
In addition to planar UTM projection math, the service calculates geodesic ellipsoidal length and area using `pyproj.Geod(ellps="WGS84")` for high precision validation.

---

## 🏗️ Architecture & Processing Pipeline

```
┌─────────────────┐       ┌────────────────────┐       ┌────────────────────────┐
│  Upload File    │ ───►  │  File Storage &    │ ───►  │    File Processor      │
│  (.zip / .kml)  │       │  Validation        │       │  (Fiona / GeoPandas)   │
└─────────────────┘       └────────────────────┘       └────────────────────────┘
                                                                    │
                                                                    ▼
┌─────────────────┐       ┌────────────────────┐       ┌────────────────────────┐
│ SQLAlchemy DB   │ ◄───  │ Measurement Engine │ ◄───  │    CRS Service         │
│ (SQLite/Postgres│       │ (Planar + Geodesic)│       │  (Auto UTM Projection) │
└─────────────────┘       └────────────────────┘       └────────────────────────┘
```

1. **API Layer (`app/api/endpoints/files.py`)**: Validates upload format/size, persists binary to storage directory, and instantiates async DB tracking record.
2. **File Processing Engine (`app/services/file_processor.py`)**:
   - For `.zip`: Unpacks Shapefile components (`.shp`, `.shx`, `.dbf`, `.prj`) to temporary isolated workspace, reads features with `geopandas.read_file()`.
   - For `.kml`: Uses Fiona driver with fallback to custom ElementTree XML parser supporting namespaced Placemark elements.
3. **CRS Service (`app/services/crs_service.py`)**: Detects source CRS, computes dataset centroid, determines optimal UTM projected CRS, and executes coordinate transformations.
4. **Measurement Service (`app/services/measurement_service.py`)**: Repairs geometry if invalid, calculates planar area ($m^2$, ha, $km^2$) and length ($m$, $km$), computes geodesic metrics, and records status notes.
5. **Persistence (`app/database.py` & `app/models/`)**: Stores file records and feature measurements relationally with SQLAlchemy 2.0 Async Engine.

---

## 🚀 API Endpoint Documentation

### 1. Upload File
`POST /api/files/`
Uploads and processes a `.zip` Shapefile or `.kml` file.

**Request:** `multipart/form-data` with key `file`

**Response (`201 Created`):**
```json
{
  "id": "7e62054c5af9",
  "filename": "survey.kml",
  "feature_count": 3,
  "crs": "EPSG:4326",
  "projected_crs": "EPSG:32643",
  "status": "COMPLETED",
  "message": "File processed and measurements calculated successfully."
}
```

---

### 2. File Information
`GET /api/files/{id}/`
Returns metadata and status for an uploaded file.

**Response (`200 OK`):**
```json
{
  "id": "7e62054c5af9",
  "filename": "survey.kml",
  "file_type": ".kml",
  "file_size": 1304,
  "feature_count": 3,
  "crs": "EPSG:4326",
  "projected_crs": "EPSG:32643",
  "status": "COMPLETED",
  "error_message": null,
  "created_at": "2026-10-07T11:37:38.011Z"
}
```

---

### 3. Feature Measurements
`GET /api/files/{id}/measurements/`
Returns metric measurements and aggregate statistics for all features.

**Response (`200 OK`):**
```json
{
  "file_id": "7e62054c5af9",
  "filename": "survey.kml",
  "crs": "EPSG:4326",
  "projected_crs": "EPSG:32643",
  "summary": {
    "total_features": 3,
    "polygon_count": 1,
    "linestring_count": 1,
    "point_count": 1,
    "other_count": 0,
    "total_area_sq_m": 37210.45,
    "total_area_hectares": 3.721045,
    "total_area_sq_km": 0.03721,
    "total_length_m": 2450.12,
    "total_length_km": 2.45012
  },
  "features": [
    {
      "feature_index": 0,
      "feature_id": "Central Farm Parcel",
      "geometry_type": "Polygon",
      "crs": "EPSG:4326",
      "measurement_status": "CALCULATED",
      "area": {
        "sq_meters": 37210.45,
        "hectares": 3.721045,
        "sq_km": 0.03721
      },
      "length": {
        "meters": 772.3,
        "kilometers": 0.7723
      },
      "geodesic": {
        "geodesic_area_sq_m": 37208.12,
        "geodesic_length_m": 772.15
      },
      "properties": {
        "Name": "Central Farm Parcel",
        "Description": "Agricultural land polygon"
      },
      "notes": null
    }
  ]
}
```

---

### 4. Vector GeoJSON FeatureCollection
`GET /api/files/{id}/geojson/`
Returns standard GeoJSON FeatureCollection with calculated measurement properties attached to each feature for visual rendering.

---

### 5. List Files
`GET /api/files/`
Returns list of all uploaded file records.

---

### 6. Delete File
`DELETE /api/files/{id}/`
Deletes uploaded file and associated records from disk and database.

---

## 🛠️ Local Setup Guide

### Prerequisites
- Python 3.10+
- Node.js v18+ & npm
- GDAL C libraries (bundled with `fiona` / `pyogrio` wheels or installed via OS package manager)

### 1. Clone Repository & Setup Backend
```bash
# Activate Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Install Dependencies
pip install -r backend/requirements.txt greenlet pydantic-settings aiosqlite

# Generate Sample KML & Shapefile datasets
python backend/sample_data/create_samples.py

# Run Pytest Test Suite
pytest

# Start FastAPI Server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
FastAPI server will start at `http://localhost:8000`. Access Swagger UI docs at `http://localhost:8000/api/docs`.

### 2. Run Frontend Web Dashboard
```bash
cd frontend
npm install
npm run dev
```
Open browser at `http://localhost:3000`.

---

## 🐳 Docker Deployment

To build and launch both Backend and Frontend in containerized mode with Docker Compose:

```bash
docker compose up --build
```

- **Frontend UI**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/api/docs`

---

## 💡 Key Design Decisions & Alternatives Considered

1. **FastAPI vs. Django REST Framework**:
   - *Decision*: Selected **FastAPI** due to native `asyncio` execution, auto-generated OpenAPI schemas, lower memory overhead, and seamless integration with Pydantic v2 type safety.
2. **Dynamic UTM Zone Selection vs. Fixed EPSG:3857 (Web Mercator)**:
   - *Decision*: Web Mercator (EPSG:3857) introduces significant area distortion away from the equator (up to 100%+ distortion near poles). Selected dynamic local UTM Zone projection (`EPSG:326XX` / `EPSG:327XX`) based on dataset centroid longitude/latitude to deliver sub-meter area precision.
3. **GeoPandas & Fiona with Custom XML Fallback**:
   - *Decision*: In minimal container environments where GDAL's `libkml` driver may be missing, direct `geopandas.read_file("file.kml")` can fail. Built a fallback XML ElementTree KML parser to guarantee 100% reliability for `.kml` uploads across all OS environments.
4. **Asynchronous SQLite (aiosqlite) with PostGIS Compatibility**:
   - *Decision*: Uses SQLAlchemy 2.0 Async Engine with SQLite for zero-config local execution, while keeping data models fully compatible with PostgreSQL/PostGIS.

---

## 📚 Learnings & Future Scope

### Learnings
- **Geospatial Coordinate Math**: Handling angular degree distortion by computing local UTM projected CRS.
- **Robust KML Parsing**: Resolving XML namespace variations in KML files.
- **Async Python Architecture**: Managing file storage, Pydantic v2 validation, and async database transactions cleanly.

### Future Enhancements
- **PostGIS Spatial Indexing**: Integration of PostGIS `ST_Area` and `ST_Length` spatial indexes for multi-gigabyte dataset querying.
- **Celery / Redis Distributed Workers**: Background task queue processing for multi-GB Shapefiles with WebSocket progress streaming.
- **3D Geometry Support**: Z-coordinate elevation measurement (surface area and 3D slope distance calculation).
- **Cloud Storage Integration**: Direct streaming uploads to AWS S3 / Google Cloud Storage.
