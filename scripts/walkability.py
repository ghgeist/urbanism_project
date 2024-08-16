import logging
import folium
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import math

# Configure logging to output to a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='walkability.log',
    filemode='w'
)

# Retry configuration: 3 attempts with exponential backoff starting at 1 second
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type(GeocoderUnavailable))
def get_location(location_string, user_agent="location_walkability_app"):
    """Get the longitude and latitude of a location string."""
    geolocator = Nominatim(user_agent=user_agent)
    location = geolocator.geocode(location_string, country_codes='us')
    if location:
        return location.longitude, location.latitude
    logging.warning("Location not found")
    return None

def miles_to_degrees(miles, latitude):
    """Convert miles to degrees of latitude and longitude."""
    degrees_latitude = miles / 69.0
    degrees_longitude = miles / (69.0 * math.cos(math.radians(latitude)))
    return degrees_latitude, degrees_longitude

def get_walkability_data(location_string, buffer_size, conn):
    """Fetch walkability data within a buffer radius around a location."""
    location = get_location(location_string)
    if not location:
        return None
    longitude, latitude = location
    degrees_latitude, degrees_longitude = miles_to_degrees(buffer_size, latitude)
    buffer_radius_degrees = max(degrees_latitude, degrees_longitude)

    query = """
        SELECT 
            geoid20,
            d2a_ranked,
            d2b_ranked, 
            d3b_ranked, 
            d4a_ranked,
            natwalkind, 
            geometry
        FROM national_walkability_index
        WHERE ST_DWithin(
            st_setsrid(st_makepoint(:longitude, :latitude), 4326),
            geometry,
            :buffer_radius_degrees
        );
    """
    df = conn.query(
        query,
        ttl="10m",
        params={"longitude": longitude, "latitude": latitude, "buffer_radius_degrees": buffer_radius_degrees}
    )
    gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkb(df['geometry']))
    gdf.set_crs(epsg=4326, inplace=True)
    return gdf

def calculate_zoom_level(buffer_size):
    """Calculate an appropriate zoom level based on the buffer size in miles."""
    # This formula is a rough approximation. Adjust the constants as needed.
    return int(14 - math.log(buffer_size + 1, 2))

def create_map(location, gdf, buffer_size):
    """Create a folium map with a choropleth layer based on walkability data and add markers for each location."""
    if not location or gdf.empty:
        return None
    longitude, latitude = location
    
    # Calculate the zoom level based on the buffer size
    zoom_level = calculate_zoom_level(buffer_size)
    
    m = folium.Map(location=[latitude, longitude], zoom_start=zoom_level, width="100%", height="100%")

    folium.Choropleth(
        geo_data=gdf,
        name='choropleth',
        data=gdf,
        columns=['geoid20', 'natwalkind'],
        key_on='feature.properties.geoid20',
        fill_color='RdYlBu',
        fill_opacity=0.5,
        line_opacity=0.2,
        legend_name='National Walkability Index',
        threshold_scale=[1, 5, 10, 15, 20]
    ).add_to(m)

    folium.GeoJson(
        gdf,
        name='geojson',
        style_function=lambda feature: {'color': 'black', 'weight': 1, 'fillOpacity': 0}
    ).add_to(m)

    for _, row in gdf.iterrows():
        centroid = row.geometry.centroid
        folium.Circle(
            location=[centroid.y, centroid.x],
            radius=40,  # Adjust the radius as needed
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.6,
            popup=f"Block Group ID: {row['geoid20']}<br>NatWalkInd: {round(row['natwalkind'], 1)}"
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m