import geopandas as gpd

file_path = r'data\WalkabilityIndex\Natl_WI.gdb'

print("Reading the file from:", file_path)
gdf = gpd.read_file(file_path)
print("File read successfully.")

csv_path_with_geometry = r'data\WalkabilityIndex\Natl_WI.csv'
print("Saving GeoDataFrame to CSV with geometry at:", csv_path_with_geometry)
gdf.to_csv(csv_path_with_geometry, index=False)
print("GeoDataFrame saved to CSV with geometry.")

print("Dropping 'geometry' column.")
gdf.drop(columns='geometry', inplace=True)
print("'geometry' column dropped.")

csv_path_without_geometry = r'data\WalkabilityIndex\Natl_WI_no_geometry.csv'
print("Saving GeoDataFrame to CSV without geometry at:", csv_path_without_geometry)
gdf.to_csv(csv_path_without_geometry, index=False)
print("GeoDataFrame saved to CSV without geometry.")