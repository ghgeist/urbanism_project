import math
import json
import logging
import os
import re
import sys
import time
from functools import lru_cache

import geopandas as gpd
import pandas as pd
import psycopg2
from geopy.exc import GeocoderUnavailable
from geopy.geocoders import Nominatim
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from services.db import get_db_connection
from services.db import is_connection_closed as _is_connection_closed

DEBUG_LOG_ENV = "WALKABILITY_DEBUG_LOG"
_DEBUG_LOGGER = logging.getLogger("walkability.debug")

def log_debug(location, message, data=None, hypothesis_id=None):
    """Emit a structured debug log when WALKABILITY_DEBUG_LOG=1 is set."""
    if os.environ.get(DEBUG_LOG_ENV) != "1":
        return
    if not _DEBUG_LOGGER.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            stream=sys.stdout,
        )
    payload = {
        "location": location,
        "message": message,
        "data": data,
        "timestamp_ms": int(time.time() * 1000),
        "hypothesis_id": hypothesis_id,
    }
    try:
        _DEBUG_LOGGER.info(json.dumps(payload, default=str))
    except (TypeError, ValueError) as exc:
        fallback = {
            "location": location,
            "message": "debug log serialization failed",
            "error": str(exc),
        }
        _DEBUG_LOGGER.info(json.dumps(fallback, default=str))

# UK→US spelling variants for US geocoding (Nominatim/OSM often use US spelling).
_US_STREET_SPELLING = [
    ("harbour", "harbor"),
    ("centre", "center"),
    ("colour", "color"),
    ("favour", "favor"),
    ("behaviour", "behavior"),
]


def _normalize_us_street_spelling(location_string):
    """
    Normalize common UK spellings to US for geocoding (Nominatim/OSM often use US spelling in the US).
    Returns a new string; does not modify in place.
    """
    if not location_string or not isinstance(location_string, str):
        return location_string
    s = location_string
    for uk, us in _US_STREET_SPELLING:
        # Case-insensitive whole-word replacement (e.g. harbour → harbor)
        s = re.sub(rf"\b{re.escape(uk)}\b", us, s, flags=re.IGNORECASE)
    return s


# Module-level geolocator reuses the underlying HTTP session across calls.
_geolocator = Nominatim(user_agent="location_walkability_app")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(GeocoderUnavailable)
)
def _geocode_nominatim(query):
    """Thin wrapper around Nominatim.geocode that tenacity can retry."""
    return _geolocator.geocode(query, country_codes="us")


@lru_cache(maxsize=256)
def get_location(location_string, user_agent="location_walkability_app"):
    """
    Geocode the location string using Nominatim and return (longitude, latitude).
    Tries the string as-is first; if not found, retries with US street spelling normalized
    (e.g. harbour → harbor) so UK-spelled street names match OSM data.

    Results are cached (LRU, 256 entries) so repeated queries for the same
    string avoid redundant network round-trips.
    """
    location = _geocode_nominatim(location_string)
    if location:
        return location.longitude, location.latitude
    normalized = _normalize_us_street_spelling(location_string)
    if normalized != location_string:
        location = _geocode_nominatim(normalized)
        if location:
            return location.longitude, location.latitude
    logging.warning("Location not found (geocode returned no result)")
    return None

def validate_location_input(location_string):
    """
    Validate location input before geocoding.
    Returns (is_valid, error_message).
    The API enforces the same max length (200) via Query(max_length=200) in api/main.py.
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

def _rows_to_gdf(rows, columns):
    """Convert SQL query results into a typed GeoDataFrame."""
    df = pd.DataFrame(rows, columns=columns)
    if df.empty:
        gdf = gpd.GeoDataFrame(df, geometry=[])
        gdf.set_crs(epsg=4326, inplace=True)
        return gdf

    geometry_data = df['geometry'].apply(lambda x: bytes(x) if isinstance(x, memoryview) else x)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkb(geometry_data))

    numeric_columns = ['d2a_ranked', 'd2b_ranked', 'd3b_ranked', 'd4a_ranked', 'natwalkind', 'dist_miles']
    for col in numeric_columns:
        if col in gdf.columns:
            gdf[col] = pd.to_numeric(gdf[col], errors='coerce')

    gdf.set_crs(epsg=4326, inplace=True)
    return gdf

def query_walkability_by_coords(lon, lat, radius_miles, conn=None):
    """
    Query walkability block groups around a lon/lat point using geography distance.

    Distance is computed by PostGIS as the minimum distance from origin point to
    polygon boundary in miles (0 if the point lies inside the polygon).
    """
    is_valid, error_msg = validate_buffer_size(radius_miles)
    if not is_valid:
        logging.error(f"Invalid radius miles: {error_msg}")
        raise ValueError(f"Invalid radius miles: {error_msg}")

    radius_meters = float(radius_miles) * 1609.344
    # Index-friendly bbox prefilter in degrees, then exact geography distance in meters.
    deg_lat, deg_lon = miles_to_degrees(radius_miles, lat)
    bbox_radius_degrees = max(deg_lat, deg_lon)

    should_close_conn = False
    if conn is None:
        conn = get_db_connection()
        should_close_conn = True

    try:
        if _is_connection_closed(conn):
            raise psycopg2.InterfaceError("Connection is closed")

        query = """
            SELECT
                geoid20,
                d2a_ranked,
                d2b_ranked,
                d3b_ranked,
                d4a_ranked,
                natwalkind,
                ST_AsBinary(geometry) AS geometry,
                ST_Distance(
                    geometry::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) / 1609.344 AS dist_miles
            FROM national_walkability_index
            WHERE geometry && ST_Expand(
                ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                %s
            )
            AND ST_DWithin(
                geometry::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s
            );
        """

        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (lon, lat, lon, lat, bbox_radius_degrees, lon, lat, radius_meters),
            )
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return _rows_to_gdf(rows, columns)
    finally:
        if should_close_conn and conn:
            conn.close()

def get_walkability_data(location_string, buffer_size, conn=None):
    """
    Fetch walkability data within a given buffer radius around the stated location.

    Args:
        location_string: Address, ZIP code, or city name
        buffer_size: Buffer radius in miles
        conn: psycopg2 connection, or None.
              If None, creates a new connection via get_db_connection() and
              closes it when done (try/finally). If provided, caller owns
              the lifecycle — this function will not close it.

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
    log_debug("walkability.py:get_walkability_data", "delegating query to coordinate search", {
        "longitude": longitude,
        "latitude": latitude,
        "buffer_size_miles": buffer_size,
    }, "A")
    return query_walkability_by_coords(longitude, latitude, buffer_size, conn=conn)
