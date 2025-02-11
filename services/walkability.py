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

@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=1, max=10), 
    retry=retry_if_exception_type(GeocoderUnavailable)
)
def get_location(location_string, user_agent="location_walkability_app"):
    """
    Geocode the location string using Nominatim and return (longitude, latitude).
    """
    geolocator = Nominatim(user_agent=user_agent)
    location = geolocator.geocode(location_string, country_codes='us')
    if location:
        return location.longitude, location.latitude
    logging.warning("Location not found for: %s", location_string)
    return None

def miles_to_degrees(miles, latitude):
    """
    Convert a distance (miles) to degrees (latitude & longitude).
    """
    degrees_latitude = miles / 69.0
    degrees_longitude = miles / (69.0 * math.cos(math.radians(latitude)))
    return degrees_latitude, degrees_longitude

def get_walkability_data(location_string, buffer_size, conn):
    """
    Fetch walkability data within a given buffer radius around the stated location.
    """
    location = get_location(location_string)
    if not location:
        return None
    longitude, latitude = location
    degrees_latitude, degrees_longitude = miles_to_degrees(buffer_size, latitude)
    buffer_radius_degrees = max(degrees_latitude, degrees_longitude)

    # I can remove the d2a_ranked, d2b_ranked, d3b_ranked, d4a_ranked columns if I don't want to show them in the popup
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
    """
    Calculate an appropriate zoom level for the map based on the buffer size (in miles).
    """
    return int(14 - math.log(buffer_size + 1, 2))

def create_map(location, gdf, buffer_size):
    """
    Create a Folium map with a choropleth layer overlaying walkability data.
    """
    if not location or gdf.empty:
        return None
    longitude, latitude = location
    zoom_level = calculate_zoom_level(buffer_size)

    # Create the base Folium map
    m = folium.Map(location=[latitude, longitude], zoom_start=zoom_level, width="100%", height="100%")

    # Add choropleth layer
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

    # Add detailed GeoJSON layer
    folium.GeoJson(
        gdf,
        name='geojson',
        style_function=lambda feature: {'color': 'black', 'weight': 1, 'fillOpacity': 0}
    ).add_to(m)

    # Add markers for each block group
    for _, row in gdf.iterrows():
        centroid = row.geometry.centroid
        folium.Circle(
            location=[centroid.y, centroid.x],
            radius=40,  # Customize as needed
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.6,
            popup=f"Block Group ID: {row['geoid20']}<br>NatWalkInd: {round(row['natwalkind'], 1)}"
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m 