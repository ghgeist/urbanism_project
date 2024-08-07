import os
import asyncio
import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Set the OpenAI API key from Streamlit secrets
os.environ["OPENAI_API_KEY"] = st.secrets["openai"]["openai_api_key"]

# Read database connection details from Streamlit secrets
db_secrets = st.secrets["connections"]["postgresql"]
username = db_secrets["username"]
password = db_secrets["password"]
hostname = db_secrets["host"]
port_number = db_secrets["port"]
db_name = db_secrets["database"]

# Create the PostgreSQL URI
postgres_uri = f"postgresql+psycopg2://{username}:{password}@{hostname}:{port_number}/{db_name}"

# Create an SQLDatabase instance from the URI
db = SQLDatabase.from_uri(postgres_uri)

# Store the database instance in session state
if "db" not in st.session_state:
    st.session_state.db = db

# Asynchronous function to get an answer by SQL query using OpenAI chat model
async def get_answer_by_sql_query(input):
    try:
        # Retrieve the database instance from session state
        db = st.session_state.db
        
        # Initialize the OpenAI chat model
        llm = ChatOpenAI(model="gpt-4", temperature=0)
        # Create an SQL agent with the model and database
        agent_executor = create_sql_agent(llm, db=db, verbose=True)
        
        # Invoke the agent with the input query and get the response
        response = agent_executor.invoke({"input": input})
        return response
    except Exception as e:
        return {"output": f"An error occurred: {str(e)}"}