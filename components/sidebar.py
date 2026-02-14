import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.title("Exploring the U.S. National Walkability Index")
        city_name = st.text_input("Enter a U.S. Address, Zip Code or City:", "Knoxville, TN")
        buffer_radius_miles = st.slider(
            "Select buffer radius (miles)",
            min_value=0.1,
            max_value=10.0,
            value=0.5,
            step=0.1
        )
        min_search_radius = round(buffer_radius_miles + 0.1, 1)
        default_search_radius = max(3.0, min_search_radius)
        search_radius_miles = st.slider(
            "Select search radius (miles)",
            min_value=min_search_radius,
            max_value=25.0,
            value=min(default_search_radius, 25.0),
            step=0.1
        )
        min_delta = st.slider(
            "Minimum NWI improvement delta",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.5
        )
        st.write(
            """The U.S. National Walkability Index (NWI) is a metric developed by the U.S. Environmental Protection Agency (EPA)
            to evaluate the walkability of neighborhoods. The index ranges from 1 to 20, with higher values indicating greater walkability.
            The map displays the NWI per neighborhood within a buffer radius around the selected location.
            More information can be found [here](https://www.epa.gov/smartgrowth/national-walkability-index-user-guide-and-methodology)
            """
        )
    return city_name, buffer_radius_miles, search_radius_miles, min_delta
