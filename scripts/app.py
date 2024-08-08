import streamlit as st
from utils import write_message
from scripts.manage_agents import generate_response
import openai

# Page Config for "CityBot"
st.set_page_config(
    page_title="CityBot", 
    page_icon="🌆",
    layout="wide",
    menu_items={
    'About': 
    """
    https://github.com/ghgeist/urbanism_project"
    """
}
)

# Set up Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi, I'm CityBot! Let's talk about cities with an analytical bent!"},
    ]

# Submit handler
def handle_submit(message):
    # Handle the response
    with st.spinner('Thinking...'):
        # Call the agent
        response = generate_response(message)
        write_message('assistant', response)

# Display messages in Session State
for message in st.session_state.messages:
    write_message(message['role'], message['content'], save=False)

# Handle any user input
if question := st.chat_input("Let's build strong towns!"):
    # Display user message in chat message container
    write_message('user', question)

    # Generate a response
    handle_submit(question)