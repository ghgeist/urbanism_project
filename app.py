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
        'About': "https://www.linkedin.com/in/grantgeist/"
    }
)

def main():
    # Create a two-column layout
    col1, col2 = st.columns([1, 2])  # 1/3 for controls and chat, 2/3 for the map

    with col1:
        st.subheader("Map Controls")
        city_name = st.text_input("Enter a U.S. Address, Zip Code or City:", "Knoxville, TN")
        buffer_radius_miles = st.slider(
            "Select buffer radius (miles)", 
            min_value=0.1, max_value=10.0, value=0.5, step=0.1
        )

        # # Chat interface
        # nl_query = render_nl_query()
        # if nl_query:
        #     st.write("Query received, ready to process")
        #     # Here you would handle the query processing
        #     # Example: results = execute_nl_query(nl_query, conn)
        #     # st.dataframe(results)

    with col2:
        # Render the map
        # Render main content based on the inputs
        render_main_content(city_name, buffer_radius_miles)


if __name__ == "__main__":
    main() 