import streamlit as st
from streamlit_folium import folium_static
import walkability

# Set the page configuration to wide mode
st.set_page_config(layout="wide")

# Create a two-column layout
map_col, chat_col = st.columns([2, 1])

with chat_col:
    # Create a text input widget for the city name
    city_name = st.text_input("Enter a U.S. city name", "Knoxville")
    
    # Create a slider for the buffer radius in miles
    buffer_radius_miles = st.slider("Select buffer radius (miles)", min_value=0.1, max_value=10.0, value=0.5, step=0.1)

def main():
    # Hardcoded file path for the GeoDataFrame
    filepath = r'data\WalkabilityIndex\Natl_WI.gdb'
    
    if city_name:
        gdf = walkability.load_geodataframe(filepath)
        location = walkability.get_city_location(city_name)
        
        if location:
            city_gdf = walkability.filter_geodataframe_by_city(gdf, location, buffer_radius_miles)
            city_gdf = walkability.simplify_geometries(city_gdf)
            walkability.display_walkability_index(city_gdf)
            walkability.calculate_memory_usage(city_gdf)
            with map_col:
                m = walkability.create_map(city_gdf, location, buffer_radius_miles)
                folium_static(m)
        else:
            st.write("City not found. Please enter a valid city name.")

if __name__ == "__main__":
    main()