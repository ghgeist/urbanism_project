import streamlit as st
import folium
from streamlit.components.v1 import html
from geopy.geocoders import Nominatim

# Set the page configuration to wide mode
st.set_page_config(layout="wide")

# Create a two-column layout
map, chat = st.columns([2, 1])

with chat:
    # Create a text input widget for the city name
    city = st.text_input("Enter a city name", "Istanbul")

# Initialize the geolocator
geolocator = Nominatim(user_agent="streamlit_app")

# Get the location of the entered city
location = geolocator.geocode(city)

# Create the Folium map with the new location
m = folium.Map(
    location=[location.latitude, location.longitude],
    width="100%",
    height="100%",
    zoom_start=10
)

# Convert the map to HTML
map_html = m._repr_html_()

with map:
    # Display the map in Streamlit
    st.components.v1.html(map_html, height=500)