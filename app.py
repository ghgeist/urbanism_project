from dotenv import load_dotenv
load_dotenv()
import streamlit as st
from components.chat_interface import render_chat_interface

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
    render_chat_interface()

if __name__ == "__main__":
    main() 