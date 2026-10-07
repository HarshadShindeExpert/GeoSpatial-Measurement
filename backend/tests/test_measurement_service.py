import pytest
from shapely.geometry import Polygon, LineString, Point, GeometryCollection
from app.services.measurement_service import MeasurementService
from app.models.feature_record import MeasurementStatus

@pytest.fixture
def measurement_service():
    return MeasurementService()

def test_polygon_area_and_length(measurement_service):
    # A square polygon in UTM projection (100m x 100m)
    # 100m x 100m = 10,000 m² = 1 hectare = 0.01 km²
    poly_wgs84 = Polygon([(77.2000, 28.6000), (77.2010, 28.6000), (77.2010, 28.6010), (77.2000, 28.6010), (77.2000, 28.6000)])
    
    result = measurement_service.process_feature_measurement(
        geometry=poly_wgs84,
        source_crs="EPSG:4326",
        projected_crs="EPSG:32643"
    )

    assert result["measurement_status"] == MeasurementStatus.CALCULATED
    assert result["area_sq_m"] > 0
    assert result["area_hectares"] > 0
    assert result["area_sq_km"] > 0
    assert result["length_m"] > 0
    assert result["geodesic_area_sq_m"] is not None

def test_linestring_length(measurement_service):
    line_wgs84 = LineString([(77.2000, 28.6000), (77.2050, 28.6050)])
    
    result = measurement_service.process_feature_measurement(
        geometry=line_wgs84,
        source_crs="EPSG:4326",
        projected_crs="EPSG:32643"
    )

    assert result["measurement_status"] == MeasurementStatus.CALCULATED
    assert result["length_m"] > 0
    assert result["length_km"] > 0
    assert result["area_sq_m"] == 0.0

def test_point_no_measurement(measurement_service):
    point = Point(77.2090, 28.6139)
    
    result = measurement_service.process_feature_measurement(
        geometry=point,
        source_crs="EPSG:4326",
        projected_crs="EPSG:32643"
    )

    assert result["measurement_status"] == MeasurementStatus.NOT_APPLICABLE
    assert result["area_sq_m"] is None
    assert result["length_m"] is None
    assert "Point geometries do not have area or length" in result["notes"]

def test_invalid_geometry_graceful_recovery(measurement_service):
    # Self-intersecting bowtie polygon (invalid geometry)
    bowtie = Polygon([(0, 0), (0, 2), (2, 0), (2, 2), (0, 0)])
    
    result = measurement_service.process_feature_measurement(
        geometry=bowtie,
        source_crs="EPSG:4326",
        projected_crs="EPSG:32643"
    )

    assert result["measurement_status"] == MeasurementStatus.CALCULATED
    assert result["notes"] is not None
    assert "repaired" in result["notes"].lower()
