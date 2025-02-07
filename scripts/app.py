import streamlit as st
from streamlit_folium import folium_static
from walkability import get_location, get_walkability_data, create_map

# Set the page configuration to wide mode
st.set_page_config(
    page_title="Exploring the U.S. National Walkability Index",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "https://www.linkedin.com/in/grantgeist/"
    }
)

# Cache the get_location function
@st.cache_data
def cached_get_location(city_name):
    return get_location(city_name)

# Cache the get_walkability_data function
@st.cache_data
def cached_get_walkability_data(city_name, buffer_radius_miles, _conn):
    return get_walkability_data(city_name, buffer_radius_miles, _conn)

# -----------------------------
# New helper function for sidebar rendering
def render_sidebar():
    with st.sidebar:
        st.title("Exploring the U.S. National Walkability Index")
        city_name = st.text_input("Enter a U.S. Address, Zip Code or City:", "Knoxville, TN")
        buffer_radius_miles = st.slider(
            "Select buffer radius (miles)", 
            min_value=0.1, max_value=10.0, value=0.5, step=0.1
        )
        st.write(
            """The U.S. National Walkability Index (NWI) is a metric developed by the U.S. Environmental Protection Agency (EPA)
            to evaluate the walkability of neighborhoods. The index ranges from 1 to 20, with higher values indicating greater walkability.
            The map displays the NWI per neighborhood within a buffer radius around the selected location.
            More information can be found [here](https://www.epa.gov/smartgrowth/national-walkability-index-user-guide-and-methodology)
            """
        )
    return city_name, buffer_radius_miles

# New helper function for main content rendering
def render_main_content(city_name, buffer_radius_miles):
    if city_name:
        location = cached_get_location(city_name)
        if location:
            # Consider using a context manager for connection handling in production code.
            conn = st.connection("postgresql", type="sql")
            gdf = cached_get_walkability_data(city_name, buffer_radius_miles, conn)

            # Render the map
            m = create_map(location, gdf, buffer_size=buffer_radius_miles)
            if m:
                folium_static(m)
            else:
                st.error("Unable to create map. Please check your data.")
                
            # Render the data table
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

def main():
    # Render sidebar and collect user inputs
    city_name, buffer_radius_miles = render_sidebar()
    # Render main content based on the inputs
    render_main_content(city_name, buffer_radius_miles)

if __name__ == "__main__":
    main()