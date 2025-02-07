import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.title("Exploring the U.S. National Walkability Index")
        
        st.write(
            """
            This app visualizes the U.S. National Walkability Index and allows you to
            perform natural language queries to explore the underlying data.
            
            **To use the Natural Language Query feature:**
            - Enter your OpenAI API key below.
            - Select the OpenAI model you prefer.
            
            You can obtain an API key from [OpenAI Account API Keys](https://platform.openai.com/account/api-keys).
            """
        )
        
        # Prompt the user for OpenAI credentials
        openai_key = st.text_input("Enter your OpenAI API key:", type="password")
        model_choice = st.selectbox("Select OpenAI model", ["text-davinci-003", "gpt-3.5-turbo"], index=0)
        
        # Save these in session state for use in NL query service
        st.session_state["openai_api_key"] = openai_key
        st.session_state["openai_model"] = model_choice