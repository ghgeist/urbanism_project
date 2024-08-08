import os
import asyncio
import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain.chat_models import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent #This is an agent. We need a tool.
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Set the OpenAI API key from Streamlit secrets
os.environ["OPENAI_API_KEY"] = st.secrets["openai"]["openai_api_key"]
model = st.secrets["openai"]["openai_model"]

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
async def get_answer_by_sql_query(db, input):
    try:
        # Initialize the OpenAI chat model
        llm = ChatOpenAI(model=model, temperature=0)
        # Create an SQL agent with the model and database
        agent_executor = create_sql_agent(llm, db=db, verbose=True)
        
        # Invoke the agent with the input query and get the response
        response = agent_executor.invoke({"input": input})
        return response
    except Exception as e:
        return {"output": f"An error occurred: {str(e)}"}

def main():
    # Set the header of the Streamlit app
    st.header('Chat with your Postgres SQL Database...')
    
    # Initialize session state variables if they don't exist
    if "conversation" not in st.session_state:
        st.session_state.conversation = None

    if "activate_chat" not in st.session_state:
        st.session_state.activate_chat = True

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.chat_history = []

    # Display previous chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message['avatar']):
            st.markdown(message["content"])

    # If chat is activated, display the chat input and handle responses
    if st.session_state.activate_chat:
        if prompt := st.chat_input("Ask your question from the Database"):
            # Display the user's message
            with st.chat_message("user", avatar='👨🏻'):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "avatar": '👨🏻', "content": prompt})
            
            # Get the database instance from session state
            db = st.session_state.db
            # Run the asynchronous function to get the response
            response = asyncio.run(get_answer_by_sql_query(db, prompt))
            cleaned_response = response["output"]
            
            # Display the assistant's response
            with st.chat_message("assistant", avatar='🤖'):
                st.markdown(cleaned_response)
            st.session_state.messages.append({"role": "assistant", "avatar": '🤖', "content": cleaned_response})

# Run the main function when the script is executed
if __name__ == '__main__':
    main()