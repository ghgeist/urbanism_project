import geopandas as gpd
from geopy.geocoders import Nominatim
from shapely.geometry import Point
import folium
from collections import namedtuple
from pyproj import CRS, Transformer
import logging
import math

# Configure logging to output to a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='walkability.log',  # Log file name
    filemode='w'  # Overwrite the log file each time the script runs
)

Location = namedtuple('Location', ['longitude', 'latitude'])

def load_geodataframe(filepath):
    gdf = gpd.read_file(filepath)
    logging.info(f"Loaded {len(gdf)} records from {filepath}")
    return gdf.to_crs(epsg=3857)

def get_city_location(city_name, user_agent="city_walkability_app"):
    geolocator = Nominatim(user_agent=user_agent)
    location = geolocator.geocode(city_name)
    if location:
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        lon_3857, lat_3857 = transformer.transform(location.longitude, location.latitude)
        return Location(longitude=lon_3857, latitude=lat_3857)
    logging.warning("Location not found")
    return None

def filter_geodataframe_by_city(gdf, location, buffer_radius_miles=0.1):
    buffer_radius_meters = buffer_radius_miles * 1609.34  # Convert miles to meters
    city_point = Point(location.longitude, location.latitude)
    city_buffer = gpd.GeoDataFrame([{'geometry': city_point}], crs=gdf.crs).buffer(buffer_radius_meters).iloc[0]
    filtered_gdf = gdf[gdf.geometry.intersects(city_buffer)]
    logging.info(f"Filtered GeoDataFrame to {len(filtered_gdf)} records within {buffer_radius_miles} miles radius")
    return filtered_gdf

def simplify_geometries(gdf, tolerance=0.01):
    return gdf.copy().assign(geometry=lambda df: df.geometry.simplify(tolerance, preserve_topology=True))

def display_walkability_index(gdf):
    for _, row in gdf.iterrows():
        logging.info(f"Geometry: {row['geometry']}, NatWalkInd: {row['NatWalkInd']}")

def calculate_memory_usage(gdf):
    memory_usage_mb = gdf.memory_usage(deep=True).sum() / (1024 ** 2)
    logging.info(f"GeoDataFrame size: {memory_usage_mb:.2f} MB")


def create_map(gdf, location, buffer_size):
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    lon_4326, lat_4326 = transformer.transform(location.longitude, location.latitude)
    
    zoom_level = 13
    
    # Create the map and set the bounds
    m = folium.Map(location=[lat_4326, lon_4326], zoom_start=zoom_level, width="100%", height="100%")
    
    # Create a choropleth map
    folium.Choropleth(
        geo_data=gdf,
        name='choropleth',
        data=gdf,
        columns=['GEOID20', 'NatWalkInd'],  # Use 'GEOID20' as the unique identifier
        key_on='feature.properties.GEOID20',  # Match the unique identifier in the GeoJSON
        fill_color='RdYlBu',
        fill_opacity=0.5,
        line_opacity=0.2,
        legend_name='National Walkability Index'
    ).add_to(m)
        
    # Add GeoJson layer to show boundaries
    folium.GeoJson(
        gdf,
        name='geojson',
        style_function=lambda feature: {
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0
        }
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    
    return m