import logging
import folium
import geopandas as gpd
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import math
import psycopg2
import os

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

def validate_location_input(location_string):
    """
    Validate location input before geocoding.
    Returns (is_valid, error_message).
    """
    if not location_string or not isinstance(location_string, str):
        return False, "Location must be a non-empty string"
    
    if len(location_string.strip()) == 0:
        return False, "Location cannot be empty"
    
    if len(location_string) > 200:  # Reasonable upper bound
        return False, "Location string too long (max 200 characters)"
    
    return True, None

def validate_buffer_size(buffer_size):
    """
    Validate buffer size input.
    Returns (is_valid, error_message).
    """
    if not isinstance(buffer_size, (int, float)):
        return False, "Buffer size must be a number"
    
    if buffer_size <= 0:
        return False, "Buffer size must be positive"
    
    if buffer_size > 50:  # Reasonable upper bound (50 miles)
        return False, "Buffer size too large (max 50 miles)"
    
    return True, None

def miles_to_degrees(miles, latitude):
    """
    Convert a distance (miles) to degrees (latitude & longitude).
    """
    degrees_latitude = miles / 69.0
    degrees_longitude = miles / (69.0 * math.cos(math.radians(latitude)))
    return degrees_latitude, degrees_longitude

def get_db_connection():
    """
    Create a PostgreSQL connection using Replit's environment variables.
    Falls back to Streamlit secrets if Replit env vars are not available.
    """
    try:
        # Try Replit PostgreSQL environment variables first
        db_host = os.environ.get('PGHOST')
        db_port = os.environ.get('PGPORT')
        db_name = os.environ.get('PGDATABASE')
        db_user = os.environ.get('PGUSER')
        db_password = os.environ.get('PGPASSWORD')
        
        if all([db_host, db_port, db_name, db_user, db_password]):
            return psycopg2.connect(
                host=db_host,
                port=int(db_port) if isinstance(db_port, str) else db_port,
                database=db_name,
                user=db_user,
                password=db_password
            )
    except (TypeError, psycopg2.OperationalError) as e:
        logging.warning(f"Could not connect using Replit env vars: {e}")
    
    # Fallback: try to import streamlit and use secrets
    try:
        import streamlit as st
        db_secrets = st.secrets["connections"]["postgresql"]
        return psycopg2.connect(
            host=db_secrets["host"],
            port=db_secrets["port"],
            database=db_secrets["database"],
            user=db_secrets["username"],
            password=db_secrets["password"]
        )
    except Exception as e:
        raise Exception(f"Could not connect to database. Check Replit PostgreSQL env vars or Streamlit secrets. Error: {e}")

def get_walkability_data(location_string, buffer_size, conn=None):
    """
    Fetch walkability data within a given buffer radius around the stated location.
    
    Args:
        location_string: Address, ZIP code, or city name
        buffer_size: Buffer radius in miles
        conn: Database connection (psycopg2 connection object or Streamlit SQL connection)
              If None, will attempt to create a connection using Replit env vars or Streamlit secrets.
              Note: For best performance, pass a cached connection from @st.cache_resource.
    
    Returns:
        GeoDataFrame with walkability data, or None if location not found
    """
    # Input validation
    is_valid, error_msg = validate_location_input(location_string)
    if not is_valid:
        logging.error(f"Invalid location input: {error_msg}")
        raise ValueError(f"Invalid location input: {error_msg}")
    
    is_valid, error_msg = validate_buffer_size(buffer_size)
    if not is_valid:
        logging.error(f"Invalid buffer size: {error_msg}")
        raise ValueError(f"Invalid buffer size: {error_msg}")
    
    location = get_location(location_string)
    if not location:
        return None
    longitude, latitude = location
    degrees_latitude, degrees_longitude = miles_to_degrees(buffer_size, latitude)
    buffer_radius_degrees = max(degrees_latitude, degrees_longitude)

    # Handle both Streamlit SQL connection and direct psycopg2 connection
    if conn and hasattr(conn, 'query'):
        # Streamlit SQL connection (backward compatibility)
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
    else:
        # Direct psycopg2 connection (Replit PostgreSQL)
        # Note: If conn is provided, we use it (assumed to be cached/managed externally)
        # If None, we create a new one (for backward compatibility)
        should_close_conn = False
        if conn is None:
            conn = get_db_connection()
            should_close_conn = True
        
        try:
            query = """
                SELECT 
                    geoid20,
                    d2a_ranked,
                    d2b_ranked, 
                    d3b_ranked, 
                    d4a_ranked,
                    natwalkind, 
                    ST_AsBinary(geometry) as geometry
                FROM national_walkability_index
                WHERE ST_DWithin(
                    st_setsrid(st_makepoint(%s, %s), 4326),
                    geometry,
                    %s
                );
            """
            
            with conn.cursor() as cursor:
                cursor.execute(query, (longitude, latitude, buffer_radius_degrees))
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                df = pd.DataFrame(rows, columns=columns)
            
            # Convert geometry bytes to GeoSeries
            gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkb(df['geometry']))
        finally:
            # Only close if we created the connection ourselves
            if should_close_conn and conn:
                conn.close()
    
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