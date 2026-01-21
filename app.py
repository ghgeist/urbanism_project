import streamlit as st
from components.sidebar import render_sidebar
from components.map_display import render_main_content

# Set the page configuration to wide mode
st.set_page_config(
    page_title="Exploring the U.S. National Walkability Index",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "https://grantgeist.com/"
    }
)

def main():
    # Render sidebar and get user inputs
    city_name, buffer_radius_miles = render_sidebar()
    # Render main content based on the inputs
    render_main_content(city_name, buffer_radius_miles)

if __name__ == "__main__":
    main() 