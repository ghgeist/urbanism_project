import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import streamlit as st
import os
import logging
from collections import namedtuple
from geopy.geocoders import Nominatim
from pyproj import CRS, Transformer
from shapely.geometry import Point
import geopandas as gpd

# Configure logging to output to a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='walkability.log',  # Log file name
    filemode='w'  # Overwrite the log file each time the script runs
)

Location = namedtuple('Location', ['longitude', 'latitude'])

# Get database connection details from Streamlit secrets
db_username = st.secrets["DB_USERNAME"]
db_password = st.secrets["DB_PASSWORD"]
db_host = st.secrets["DB_HOST"]
db_name = st.secrets["DB_NAME"]

def get_db_connection():
    """
    Create a connection to the PostgreSQL database.
    """
    engine = create_engine(f'postgresql://{db_username}:{db_password}@{db_host}/{db_name}')
    return engine

def get_location(location_string, user_agent="location_walkability_app"):
    """
    Get the geographic coordinates of a location string and convert them to EPSG:3857.

    Parameters:
    location_string (str): The address or place name to geocode.
    user_agent (str): The user agent string to use for the geocoding request. Default is "location_walkability_app".

    Returns:
    Location: An object containing the longitude and latitude in EPSG:3857 coordinates if the location is found.
    None: If the location is not found.
    """
    geolocator = Nominatim(user_agent=user_agent)
    location = geolocator.geocode(location_string, country_codes='us')

    if location:
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        lon_3857, lat_3857 = transformer.transform(location.longitude, location.latitude)
        return Location(longitude=lon_3857, latitude=lat_3857)

    logging.warning("Location not found")
    return None

def filter_geodataframe_by_location(engine, table_name, location, buffer_radius_miles=0.1):
    """
    Filter the GeoDataFrame by location using SQL.

    Parameters:
    engine (Engine): SQLAlchemy engine object.
    table_name (str): The name of the table to query.
    location (Location): The location to filter by.
    buffer_radius_miles (float): The buffer radius in miles. Default is 0.1 miles.

    Returns:
    GeoDataFrame: A GeoDataFrame filtered by the specified location and buffer radius.
    """
    buffer_radius_meters = buffer_radius_miles * 1609.34  # Convert miles to meters

    # Create a point geometry for the location
    location_point = Point(location.longitude, location.latitude)

    # SQL query to filter data by location and buffer radius
    query = f"""
    SELECT *
    FROM {table_name}
    WHERE ST_DWithin(
        ST_Transform(ST_SetSRID(ST_MakePoint({location.longitude}, {location.latitude}), 3857), 4326),
        ST_Transform(geometry, 4326),
        {buffer_radius_meters}
    );
    """

    # Execute the query and load the result into a GeoDataFrame
    gdf = gpd.read_postgis(query, engine, geom_col='geometry')

    logging.info("Filtered GeoDataFrame to %s records within %s miles radius", len(gdf), buffer_radius_miles)
    return gdf

def simplify_geometries(gdf, tolerance=0.01):
    return gdf.copy().assign(geometry=lambda df: df.geometry.simplify(tolerance, preserve_topology=True))

def display_walkability_index(gdf):
    for _, row in gdf.iterrows():
        logging.info("Geometry: %s, NatWalkInd: %s", row['geometry'], row['NatWalkInd'])

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