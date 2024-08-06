import logging
from collections import namedtuple
import folium
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pyproj import Transformer
from shapely import wkb

# Configure logging to output to a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='walkability.log',  # Log file name
    filemode='w'  # Overwrite the log file each time the script runs
)

Location = namedtuple('Location', ['longitude', 'latitude'])

# Retry configuration: 3 attempts with exponential backoff starting at 1 second
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type(GeocoderUnavailable))
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

def get_walkability_data(longitude, latitude, buffer_radius_miles, conn):
    """
    Retrieve walkability data from the database within a specified buffer radius.

    Parameters:
    longitude (float): Longitude in EPSG:3857 coordinates.
    latitude (float): Latitude in EPSG:3857 coordinates.
    buffer_radius_miles (float): Buffer radius in miles.
    conn (object): Database connection object.

    Returns:
    GeoDataFrame: A GeoDataFrame containing the walkability data.
    """
    buffer_radius_meters = buffer_radius_miles * 1609.34  # Convert miles to meters
    df = conn.query(
        """
        SELECT *
        FROM national_walkability_index
        WHERE ST_DWithin(
            ST_SetSRID(ST_MakePoint(:longitude, :latitude), 3857),
            geometry,
            :buffer_radius_meters
        );
        """,
        ttl="10m", # Caches the result for 10 minutes
        params={"longitude": longitude, "latitude": latitude, "buffer_radius_meters": buffer_radius_meters}
    )

    # Convert the geometry column to Shapely geometry objects
    df['geometry'] = df['geometry'].apply(wkb.loads)

    # Convert DataFrame to GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    gdf.set_crs(epsg=3857, inplace=True)

    return gdf

def simplify_geometries(gdf, tolerance=0.01):
    """
    Simplify the geometries in a GeoDataFrame.

    Parameters:
    gdf (GeoDataFrame): The GeoDataFrame to simplify.
    tolerance (float): The tolerance for simplification. Default is 0.01.

    Returns:
    GeoDataFrame: A new GeoDataFrame with simplified geometries.
    """
    return gdf.copy().assign(geometry=lambda df: df.geometry.simplify(tolerance, preserve_topology=True))

def display_walkability_index(gdf):
    """
    Log the geometry and National Walkability Index for each row in a GeoDataFrame.

    Parameters:
    gdf (GeoDataFrame): The GeoDataFrame to log.
    """
    for _, row in gdf.iterrows():
        logging.info("Geometry: %s, NatWalkInd: %s", row['geometry'], row['natwalkind'])

def create_map(gdf, location, buffer_size):
    """
    Create a folium map with a choropleth layer based on walkability data.

    Parameters:
    gdf (GeoDataFrame): The GeoDataFrame containing walkability data.
    location (Location): The central location for the map.
    buffer_size (float): The buffer size for the map.

    Returns:
    folium.Map: A folium map object.
    """
    transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    lon_4326, lat_4326 = transformer.transform(location.longitude, location.latitude)

    zoom_level = 13

    # Create the map and set the bounds
    m = folium.Map(location=[lat_4326, lon_4326], zoom_start=zoom_level, width="100%", height="100%")

    # Define the fixed scale
    scale = [1, 5, 10, 15, 20]

    # Create a choropleth map
    folium.Choropleth(
        geo_data=gdf,
        name='choropleth',
        data=gdf,
        columns=['geoid20', 'natwalkind'],  # Use 'GEOID20' as the unique identifier
        key_on='feature.properties.geoid20',  # Match the unique identifier in the GeoJSON
        fill_color='RdYlBu',
        fill_opacity=0.5,
        line_opacity=0.2,
        legend_name='National Walkability Index',
        threshold_scale=scale  # Set the fixed scale
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