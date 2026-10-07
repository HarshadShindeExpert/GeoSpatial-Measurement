import pytest
import geopandas as gpd
from shapely.geometry import Polygon, Point
from app.services.crs_service import CRSService

def test_get_utm_epsg():
    # Delhi, India: ~77.2 E, 28.6 N -> Zone 43N (EPSG:32643)
    epsg = CRSService.get_utm_epsg(77.2, 28.6)
    assert epsg == 32643

    # London, UK: ~0.1 W, 51.5 N -> Zone 30N (EPSG:32630)
    epsg_london = CRSService.get_utm_epsg(-0.1, 51.5)
    assert epsg_london == 32630

    # Sydney, Australia: ~151.2 E, -33.8 S -> Zone 56S (EPSG:32756)
    epsg_sydney = CRSService.get_utm_epsg(151.2, -33.8)
    assert epsg_sydney == 32756

def test_determine_optimal_projected_crs():
    poly = Polygon([(77.10, 28.55), (77.11, 28.55), (77.11, 28.56), (77.10, 28.56), (77.10, 28.55)])
    gdf = gpd.GeoDataFrame({"geometry": [poly]}, crs="EPSG:4326")
    
    projected_crs = CRSService.determine_optimal_projected_crs(gdf)
    assert projected_crs == "EPSG:32643"

def test_transform_geometry():
    point_wgs84 = Point(77.2090, 28.6139)
    point_utm = CRSService.transform_geometry(point_wgs84, "EPSG:4326", "EPSG:32643")
    
    # In UTM meters, coordinates should be roughly ~716000m E, ~3167000m N
    assert point_utm.x > 100000
    assert point_utm.y > 1000000
