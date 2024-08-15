import streamlit as st
from streamlit_folium import folium_static
from walkability import get_location, get_walkability_data, create_map

# Set the page configuration to wide mode
st.set_page_config(layout="wide")

def main():
    map_col, control_col = st.columns([2, 1])

    with control_col:
        city_name = st.text_input("Enter a U.S. Address, Zip Code or City:", "Knoxville")
        buffer_radius_miles = st.slider("Select buffer radius (miles)", min_value=0.1, max_value=10.0, value=0.5, step=0.1)

    if city_name:
        location = get_location(city_name)

        if location:
            conn = st.connection("postgresql", type="sql")
            gdf = get_walkability_data(city_name, buffer_radius_miles, conn)
            
            with map_col:
                m = create_map(location, gdf)
                folium_static(m)
        else:
            st.write("City not found. Please enter a valid city name.")

if __name__ == "__main__":
    main()