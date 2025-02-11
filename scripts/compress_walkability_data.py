# Problem: The raw walkability data is ~1.4 GB. The Neon Postgres DB free tier only allows for ~500 MB. 
# The geometry is what is taking up most of the space. The file without the geometry is ~40 MB
# Challenge: Figure out how to reduce the size of the data to fit into the DB.

## The CRS needs to be 4326!!!

import geopandas as gpd
from shapely import wkt
import pandas as pd
from joblib import Parallel, delayed
import os

## This is working. Will probably need to move this elsewhere
file_path = r'data\WalkabilityIndex\Natl_WI.gdb' # This data is in NAD83 (EPSG:4269)

print("Reading the file from:", file_path)
gdf = gpd.read_file(file_path)
print("File read successfully.")

# Convert all column names to lowercase
gdf.columns = [col.lower() for col in gdf.columns]

# Detect and print the CRS
if gdf.crs:
    print("The CRS of the GeoDataFrame is:", gdf.crs)
else:
    print("The GeoDataFrame does not have a CRS.")

# Converting to EPSG:4326 because this is what we need for geographic coordinates
if gdf.crs and gdf.crs.to_epsg() != 4326:
    gdf = gdf.to_crs(epsg=4326)
    print("CRS transformed to EPSG:4326.")
else:
    gdf.set_crs(epsg=4326, allow_override=True)
    print("CRS set to EPSG:4326.")

# Convert geometries to WKT format
gdf['geometry'] = gdf['geometry'].apply(lambda geom: geom.wkt)

csv_path_with_geometry = r'data\WalkabilityIndex\Natl_WI.csv'
print("Saving GeoDataFrame to CSV with geometry in WKT format at:", csv_path_with_geometry)
gdf.to_csv(csv_path_with_geometry, index=False)
print("GeoDataFrame saved to CSV with geometry in WKT format.")

gdf.head(n=1)


## This works
# Load the walkability data using pandas
df = pd.read_csv(r'data\WalkabilityIndex\Natl_WI.csv')

# Convert the DataFrame to a GeoDataFrame and set the CRS to EPSG:4326
gdf = gpd.GeoDataFrame(df, geometry=df['geometry'].apply(wkt.loads), crs='EPSG:4326')

print(f"Memory usage before simplification: {gdf.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB")

# Function to simplify geometry
def simplify_geometry(geom):
    return geom.simplify(0.0002, preserve_topology=True)

# Simplify the geometries using parallel processing
gdf['geometry'] = Parallel(n_jobs=-2)(delayed(simplify_geometry)(geom) for geom in gdf['geometry'])

print(f"Memory usage after simplification: {gdf.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB")

# Convert geometries to WKT and save to CSV
gdf['geometry'] = gdf['geometry'].apply(lambda geom: geom.wkt)
gdf.to_csv(r'data\WalkabilityIndex\Natl_WI_simplified.csv', index=False)

# Print file sizes
original_file_size = os.path.getsize(r'data\WalkabilityIndex\Natl_WI.csv') / 1024 ** 2
simplified_file_size = os.path.getsize(r'data\WalkabilityIndex\Natl_WI_simplified.csv') / 1024 ** 2

print(f"Original file size: {original_file_size:.2f} MB")
print(f"Simplified file size: {simplified_file_size:.2f} MB")


# Load the walkability data using pandas
input_path = r'data\WalkabilityIndex\Natl_WI_simplified.csv'
df = pd.read_csv(input_path)

# Drop rows where cbsa_name is null
df = df.dropna(subset=['cbsa_name'])

# Convert the DataFrame to a GeoDataFrame
gdf = gpd.GeoDataFrame(df, geometry=df['geometry'].apply(wkt.loads), crs='EPSG:4326')

# Print memory usage before saving
print(f"Memory usage before saving: {gdf.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB")

# Convert geometries to WKT and save to CSV
output_path = r'data\WalkabilityIndex\Natl_WI_simplified_drop_cols.csv'
gdf['geometry'] = gdf['geometry'].apply(lambda geom: geom.wkt)
gdf.to_csv(output_path, index=False)

# Print memory usage after saving
print(f"Memory usage after saving: {gdf.memory_usage(deep=True).sum() / 1024 ** 2:.2f} MB")

# Print file sizes
original_file_size = os.path.getsize(input_path) / 1024 ** 2
simplified_file_size = os.path.getsize(output_path) / 1024 ** 2

print(f"Original file size: {original_file_size:.2f} MB")
print(f"Simplified file size: {simplified_file_size:.2f} MB")

# Ensure the geoid20 column is treated as strings
gdf.loc[:, 'geoid20'] = gdf['geoid20'].astype(str)

# Calculate the minimum and maximum length of the geoid20 column
min_length = gdf['geoid20'].str.len().min()
max_length = gdf['geoid20'].str.len().max()

print(f"Minimum length of geoid20: {min_length}")
print(f"Maximum length of geoid20: {max_length}")

min_value = gdf['natwalkind'].min()
max_value = gdf['natwalkind'].max()
print(f"Minimum natwalkind: {min_value}")
print(f"Maximum natwalkind: {max_value}")

# This results in a pretty good estimate of the database. 
def calculate_data_sizes(df):
    # Specify the columns in the dataframe
    columns = ['geoid20', 'natwalkind', 'geometry']
    df = df.loc[:, columns]  # Use .loc to avoid SettingWithCopyWarning
    total_rows = len(df)
    
    # Convert the geometry column to Shapely objects
    df.loc[:, 'geometry'] = df['geometry'].apply(wkt.loads)
    
    # Calculate actual average size of each column
    geoid20_size_bytes = df['geoid20'].apply(lambda x: len(str(x).encode('utf-8'))).mean()
    geoid20_size_mb = geoid20_size_bytes / (1024 * 1024)
    
    natwalkind_size_bytes = df['natwalkind'].apply(lambda x: 4).mean()  # NUMERIC(4, 2) is 4 bytes
    natwalkind_size_mb = natwalkind_size_bytes / (1024 * 1024)
    
    # For geometry, we need to load it as a GeoDataFrame to calculate the actual size
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    
    # Set the initial CRS (assuming the initial CRS is EPSG:4326, change if different)
    gdf.set_crs(epsg=4326, inplace=True)
    
    # Calculate the average size of the geometries in bytes
    geometry_size_bytes = gdf['geometry'].apply(lambda x: len(x.wkb)).mean()
    geometry_size_mb = geometry_size_bytes / (1024 * 1024)
    
    # Calculate size per row
    size_per_row_mb = geoid20_size_mb + natwalkind_size_mb + geometry_size_mb
    
    # Calculate total data size (in MB)
    total_data_size_mb = size_per_row_mb * total_rows
    
    # Estimate index size (25% of data size)
    index_size_mb = total_data_size_mb * 0.25
    
    # Estimate overhead (10% of data size)
    overhead_mb = total_data_size_mb * 0.10
    
    # Total estimated database size
    total_db_size_mb = total_data_size_mb + index_size_mb + overhead_mb
    
    # Create a DataFrame with the results
    results = pd.DataFrame({
        'Metric': [
            'Total rows',
            'Average geoid20 size (MB)',
            'Average natwalkind size (MB)',
            'Average geometry size (MB)',
            'Estimated total data size (MB)',
            'Estimated total index size (MB)',
            'Estimated total overhead (MB)',
            'Estimated database size (MB)'
        ],
        'Value': [
            total_rows,
            geoid20_size_mb,
            natwalkind_size_mb,
            geometry_size_mb,
            total_data_size_mb,
            index_size_mb,
            overhead_mb,
            total_db_size_mb
        ]
    })
    
    return results

# Call the function
filepath_1 = r'data\WalkabilityIndex\Natl_WI_simplified.csv'
filepath_2 = r'data\WalkabilityIndex\Natl_WI_simplified_drop_cols.csv'

df1 = pd.read_csv(filepath_1)
results_df1 = calculate_data_sizes(df1)

df2 = pd.read_csv(filepath_2)
results_df2 = calculate_data_sizes(df2)

# Merge the results for comparison
comparison_df = results_df1.merge(results_df2, on='Metric', suffixes=('_file1', '_file2'))

# Add a column for percent change
comparison_df['Percent Change'] = round(((comparison_df['Value_file2'] - comparison_df['Value_file1']) / comparison_df['Value_file1']) * 100, 2)

# Rename the columns
comparison_df.columns = ['Metric', 'Simplified df', 'Simplified df, dropped cols', 'Percent Change']

# Save the comparison to a CSV file
comparison_df.to_csv(r'data\db_compression_results\geometry_simplification_and_column_drop.csv', index=False)
comparison_df