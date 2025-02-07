import streamlit as st
from streamlit_folium import folium_static
from services.walkability import get_location, get_walkability_data, create_map
from tenacity import RetryError

@st.cache_data
def cached_get_location(city_name):
    return get_location(city_name)

@st.cache_data
def cached_get_walkability_data(city_name, buffer_radius_miles, _conn):
    return get_walkability_data(city_name, buffer_radius_miles, _conn)

def render_main_content(city_name, buffer_radius_miles):
    if city_name:
        try:
            location = cached_get_location(city_name)
        except RetryError:
            st.error("Geocoding service is currently unavailable. Please try again later.")
            return

        if location:
            # Consider using a context manager for connection handling in production
            conn = st.connection("postgresql", type="sql")
            gdf = cached_get_walkability_data(city_name, buffer_radius_miles, conn)
            m = create_map(location, gdf, buffer_size=buffer_radius_miles)
            if m:
                folium_static(m)
            else:
                st.error("Unable to create map. Please check your data.")
                
            df = gdf[['geoid20', 'd2a_ranked', 'd2b_ranked', 'd3b_ranked', 'd4a_ranked', 'natwalkind']].copy()
            rename_dict = {
                'geoid20': '2020 Census Block Group ID',
                'd2a_ranked': 'Employment and Housing Mix Rank',
                'd2b_ranked': 'Employment Type Rank',
                'd3b_ranked': 'Intersection Density Rank',
                'd4a_ranked': 'Commute Mode Rank',
                'natwalkind': 'National Walkability Index'
            }
            df.rename(columns=rename_dict, inplace=True)
            st.write("### National Walkability Index Components")
            st.write(
                """To score block groups, the block groups were placed into 20 quantiles by variable value (quantiles are groupings with equal numbers of records), 
                each containing 5 percent of the total block groups. Then a ranked score was assigned from 1 to 20, with 1 representing the lowest influence on walking,
                and 20 representing the highest."""
            )
            st.dataframe(df)
        else:
            st.error("City not found. Please enter a valid city name.") 