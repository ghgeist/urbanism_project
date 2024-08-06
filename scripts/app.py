import streamlit as st
from streamlit_folium import folium_static
import walkability

# Set the page configuration to wide mode
st.set_page_config(layout="wide")

# Create a two-column layout
map_col, chat_col = st.columns([2, 1])

with chat_col:
    # Create a text input widget for the city name
    city_name = st.text_input("Enter a U.S. Address, Zip Code or City:", "Knoxville")

    # Create a slider for the buffer radius in miles
    buffer_radius_miles = st.slider("Select buffer radius (miles)", min_value=0.1, max_value=10.0, value=0.5, step=0.1)

def main():
    if city_name:
        location = walkability.get_location(city_name)

        if location:
            conn = st.connection("postgresql", type="sql")
            longitude = location.longitude
            latitude = location.latitude
            
            gdf = walkability.get_walkability_data(longitude, latitude, buffer_radius_miles, conn)
            city_gdf = walkability.simplify_geometries(gdf)
            walkability.display_walkability_index(city_gdf)
            with map_col:
                m = walkability.create_map(city_gdf, location, buffer_radius_miles)
                folium_static(m)
        else:
            st.write("City not found. Please enter a valid city name.")

if __name__ == "__main__":
    main()