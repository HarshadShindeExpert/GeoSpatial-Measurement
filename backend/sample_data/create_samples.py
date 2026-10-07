import os
import zipfile
import tempfile
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point, MultiPolygon

SAMPLE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

def generate_kml():
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Survey Parcels and Tracks</name>
    <description>Sample GIS features for measurement testing</description>
    
    <Placemark>
      <name>Central Farm Parcel</name>
      <description>Agricultural land polygon</description>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              77.2090,28.6139,0
              77.2150,28.6139,0
              77.2150,28.6190,0
              77.2090,28.6190,0
              77.2090,28.6139,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>

    <Placemark>
      <name>Irrigation Canal</name>
      <description>Linear water canal</description>
      <LineString>
        <coordinates>
          77.2000,28.6100,0
          77.2050,28.6150,0
          77.2100,28.6200,0
          77.2200,28.6250,0
        </coordinates>
      </LineString>
    </Placemark>

    <Placemark>
      <name>Weather Station Alpha</name>
      <description>Point location monitoring station</description>
      <Point>
        <coordinates>77.2100,28.6160,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>"""

    kml_path = SAMPLE_DIR / "sample_polygons.kml"
    with open(kml_path, "w", encoding="utf-8") as f:
        f.write(kml_content)
    print(f"Created KML sample at: {kml_path}")
    return kml_path

def generate_shapefile_zip():
    # Create polygon sample geometries in Delhi / WGS84
    poly1 = Polygon([
        (77.1000, 28.5500),
        (77.1080, 28.5500),
        (77.1080, 28.5560),
        (77.1000, 28.5560),
        (77.1000, 28.5500)
    ])
    
    poly2 = Polygon([
        (77.1100, 28.5600),
        (77.1150, 28.5600),
        (77.1150, 28.5640),
        (77.1100, 28.5640),
        (77.1100, 28.5600)
    ])

    poly3 = Polygon([
        (77.1200, 28.5700),
        (77.1250, 28.5700),
        (77.1250, 28.5750),
        (77.1200, 28.5750),
        (77.1200, 28.5700)
    ])

    gdf = gpd.GeoDataFrame({
        "id": [101, 102, 103],
        "name": ["North Sector Parcel", "South Sector Parcel", "East Sector Parcel"],
        "category": ["Zone A", "Zone B", "Zone C"],
        "owner": ["AgriCorp Ltd", "GreenFields LLC", "State Reserve"],
        "geometry": [poly1, poly2, poly3]
    }, crs="EPSG:4326")

    zip_path = SAMPLE_DIR / "sample_shapefile.zip"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        shp_path = Path(tmpdir) / "sample_parcels.shp"
        gdf.to_file(shp_path, driver="ESRI Shapefile")

        # Zip all generated shapefile components (.shp, .shx, .dbf, .prj)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for f in Path(tmpdir).iterdir():
                zipf.write(f, arcname=f.name)

    print(f"Created Shapefile zip sample at: {zip_path}")
    return zip_path

if __name__ == "__main__":
    generate_kml()
    generate_shapefile_zip()
