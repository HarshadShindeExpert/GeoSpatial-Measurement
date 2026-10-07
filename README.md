# Geospatial File Measurement API & Web Platform 🌍📏

> A production-grade REST API and Web GIS platform built with **FastAPI**, **GeoPandas**, **PyProj**, **Shapely**, **SQLAlchemy (Async)**, and **React (TypeScript + Leaflet)** for uploading, processing, and measuring geospatial datasets (`.zip` Shapefiles and `.kml` files), featuring an enterprise **Cyber Security Protection Layer**.

---

## 🔒 Cyber Security Protection Layer

The platform is fortified with multi-layered cyber security controls guarding against OWASP Top 10 vulnerabilities:

1. **File Header Magic Bytes Verification**:
   - Inspects the raw initial bytes (`PK\x03\x04` for Zip archives, XML signatures for KML) before reading.
   - Prevents MIME-spoofing and malicious binary uploads disguised with `.zip` or `.kml` extensions.
2. **Zip Slip & Path Traversal Prevention**:
   - Inspects all archive paths during extraction to prevent arbitrary file overwrites via `../` path traversal attacks.
3. **XXE (XML External Entity) & XML Bomb Defense**:
   - Uses `defusedxml` to parse KML files safely, neutralizing entity expansion, DTD attacks, and XML bomb DoS exploits.
4. **XSS Payload Sanitization**:
   - Neutralizes `<script>`, `javascript:`, and HTML tags in feature attributes, Placemark names, and descriptions prior to rendering in Leaflet UI popups.
5. **Rate Limiting & DoS Mitigation**:
   - Sliding-window rate-limiting middleware (`RateLimiterMiddleware`) caps requests per client IP (120 general requests/min, 20 uploads/min).
6. **Hardened HTTP Security Headers**:
   - `Content-Security-Policy (CSP)`
   - `X-Frame-Options: DENY` (Clickjacking defense)
   - `X-Content-Type-Options: nosniff` (MIME sniffing defense)
   - `X-XSS-Protection: 1; mode=block`
   - `Referrer-Policy: strict-origin-when-cross-origin`
7. **Configurable API Key Layer**:
   - Optional `X-API-Key` authentication header validation (`app/security/auth.py`).

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
│  Upload File    │ ───►  │ Security Validator │ ───►  │    File Processor      │
│  (.zip / .kml)  │       │ (Magic bytes, Zip) │       │  (Fiona / GeoPandas)   │
└─────────────────┘       └────────────────────┘       └────────────────────────┘
                                                                    │
                                                                    ▼
┌─────────────────┐       ┌────────────────────┐       ┌────────────────────────┐
│ SQLAlchemy DB   │ ◄───  │ Measurement Engine │ ◄───  │    CRS Service         │
│ (SQLite/Postgres│       │ (Planar + Geodesic)│       │  (Auto UTM Projection) │
└─────────────────┘       └────────────────────┘       └────────────────────────┘
```

1. **API Layer (`app/api/endpoints/files.py`)**: Enforces rate limiting, validates upload format/size/magic bytes, persists binary to storage directory, and instantiates async DB tracking record.
2. **Security & Validation Layer (`app/security/`)**: Validates magic bytes, checks for Zip-Slip traversal, safe-parses XML via `defusedxml`, and sanitizes attributes against XSS payloads.
3. **File Processing Engine (`app/services/file_processor.py`)**: Unpacks Shapefile components or KML Placemarks safely.
4. **CRS Service (`app/services/crs_service.py`)**: Detects source CRS, computes dataset centroid, determines optimal UTM projected CRS, and executes coordinate transformations.
5. **Measurement Service (`app/services/measurement_service.py`)**: Repairs geometry if invalid, calculates planar area ($m^2$, ha, $km^2$) and length ($m$, $km$), computes geodesic metrics, and records status notes.
6. **Persistence (`app/database.py` & `app/models/`)**: Stores file records and feature measurements relationally with SQLAlchemy 2.0 Async Engine.

---

## 🚀 API Endpoint Documentation

### 1. Upload File
`POST /api/files/`
Uploads and processes a `.zip` Shapefile or `.kml` file with security magic-byte verification.

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

---

### 3. Feature Measurements
`GET /api/files/{id}/measurements/`
Returns metric measurements and aggregate statistics for all features.

---

### 4. Vector GeoJSON FeatureCollection
`GET /api/files/{id}/geojson/`
Returns standard GeoJSON FeatureCollection with sanitized measurement properties for visual map rendering.

---

## 🛠️ Local Setup Guide

```bash
# Activate Virtual Environment
.\venv\Scripts\Activate.ps1

# Install Dependencies
pip install -r backend/requirements.txt greenlet pydantic-settings aiosqlite defusedxml

# Run Pytest Test Suite
pytest -v

# Start FastAPI Server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🐳 Docker Deployment

```bash
docker compose up --build
```

- **Frontend UI**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/api/docs`
