import os
import streamlit as st
from dotenv import load_dotenv
import openai
import pandas as pd  # Make sure to import pandas for SQL execution

load_dotenv()  # This loads environment variables from your .env file into os.environ

# Helper function to securely obtain the API key
def get_api_key():
    # First, check if the API key is provided via the Streamlit session state
    if "openai_api_key" in st.session_state and st.session_state["openai_api_key"]:
        return st.session_state["openai_api_key"]
    # Otherwise, fall back to the environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key is missing. Set it in your .env file or via the Streamlit sidebar.")
    return api_key

def render_nl_query():
    st.subheader("Ask a Natural Language Query")
    nl_query = st.text_area("Enter your query in natural language:")
    return nl_query

def translate_nl_to_sql(nl_query: str, max_tokens=150, temperature=0, stop=["\n"]) -> str:
    # Set the API key centrally before making a request
    openai.api_key = get_api_key()
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use the desired model
            messages=[
                {"role": "system", "content": "You are a SQL assistant."},
                {"role": "user", "content": f"Translate the following natural language query to SQL: {nl_query}"}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=1,
            n=1,
            stop=stop
        )
        sql_query = response["choices"][0]["message"]["content"].strip()
        return sql_query
    except Exception as e:
        raise RuntimeError(f"Error processing query: {str(e)}")

def execute_nl_query(nl_query: str, conn):
    try:
        sql_query = translate_nl_to_sql(nl_query)
    except Exception as e:
        raise RuntimeError(f"NL-to-SQL translation failed: {e}")
    
    try:
        results = pd.read_sql_query(sql_query, conn)
    except Exception as e:
        raise RuntimeError(f"SQL execution failed: {e}")
    
    return results

def main():
    try:
        nl_query = render_nl_query()  # Render the NL query input area in your UI
        if nl_query:
            st.write("Query received, ready to process")
    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()