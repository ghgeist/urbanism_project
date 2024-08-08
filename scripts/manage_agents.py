from llm import llm
import re
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.schema import StrOutputParser
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool

# Import urbanism_agent_executor and postgres_agent_executor
from agents.urbanism_agent import urbanism_agent_executor
from agents.postgres_agent import pg_agent_executor

# Set up the chatbot
def get_memory(session_id):
    # Return an empty list for now, you can modify this to retrieve actual session history
    return []

def get_session_id():
    return "static_session_id"

# Initialize chat history
chat_history = []

# To Do: Figure out a beter way to determine which agent to use
def determine_agent(user_input):
    """
    Determine which agent to use based on the user input.
    """
    pattern = re.compile(r'national walkability index', re.IGNORECASE)
    if pattern.search(user_input):
        return pg_agent_executor
    else:
        return urbanism_agent_executor

def generate_response(user_input):
    """
    Create a handler that calls the appropriate agent
    and returns a response to be rendered in the UI.
    """
    global chat_history

    # Add user input to chat history
    chat_history.append({"role": "user", "content": user_input})

    # Determine which agent to use
    agent_executor = determine_agent(user_input)

    # Prepare the input for the agent executor
    input_data = {
        "input": user_input,
        "chat_history": chat_history
    }

    # Invoke the agent executor
    response = agent_executor.invoke(input_data)

    # Add agent response to chat history
    chat_history.append({"role": "agent", "content": response['output']})

    return response['output']