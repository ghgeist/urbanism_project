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

def main():

    # Move the title and control column to the sidebar
    with st.sidebar:
        st.title("Exploring the U.S. National Walkability Index")
        # Set the initial value of the text input to the random city
        city_name = st.text_input("Enter a U.S. Address, Zip Code or City:", "Knoxville, TN")
        buffer_radius_miles = st.slider("Select buffer radius (miles)", min_value=0.1, max_value=10.0, value=0.5, step=0.1)

        # Add text beneath the slider
        st.write("""The U.S. National Walkability Index (NWI) is a metric developed by the U.S. Environmental Protection Agency (EPA) to evaluate the walkability of neighborhoods.
                 The index ranges from 1 to 20, with higher values indicating greater walkability. The map displays the NWI per neighborhood within a buffer radius around the selected location.
                 More information can be found [here](https://www.epa.gov/smartgrowth/national-walkability-index-user-guide-and-methodology)
                 """)

    if city_name:
        location = cached_get_location(city_name)

        if location:
            conn = st.connection("postgresql", type="sql")
            gdf = cached_get_walkability_data(city_name, buffer_radius_miles, conn)

            # Display the map in the main area
            m = create_map(location, gdf, buffer_size=buffer_radius_miles)
            folium_static(m)

            # Create a DataFrame from the GeoDataFrame
            df = gdf[['geoid20', 'd2a_ranked', 'd2b_ranked', 'd3b_ranked', 'd4a_ranked', 'natwalkind']].copy()

            # Dictionary to rename the columns
            rename_dict = {
                'geoid20': '2020 Census Block Group ID',
                'd2a_ranked': 'Employment and Housing Mix Rank',
                'd2b_ranked': 'Employment Type Rank',
                'd3b_ranked': 'Intersection Density Rank',
                'd4a_ranked': 'Commute Mode Rank',
                'natwalkind': 'National Walkability Index'
            }

            # Rename the columns using the dictionary
            df.rename(columns=rename_dict, inplace=True)

            # Display the DataFrame as a table
            st.write("### National Walkability Index Components")
            st.write("""To score block groups, the block groups were placed into 20 quantiles by variable value (quantiles are groupings with equal numbers of records), each containing 5 percent of the total block groups. 
                     The block groups were then assigned a rank from 1 to 20 depending upon their quantile position.
                     A ranked score of 1 was assigned to the block groups with the lowest relative values influencing walking, and a ranked score of 20 was assigned to the block groups with the highest relative values influencing walking.""")
            st.dataframe(df)
        else:
            st.write("City not found. Please enter a valid city name.")

if __name__ == "__main__":
    main()