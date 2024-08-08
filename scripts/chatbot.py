from llm import llm
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.schema import StrOutputParser
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool

# Import urbanism_agent_executor from urbanism_agent.py
from agents.urbanism_agent import urbanism_agent_executor

# Set up the chatbot
def get_memory(session_id):
    # Return an empty list for now, you can modify this to retrieve actual session history
    return []

def get_session_id():
    return "static_session_id"

# Initialize chat history
chat_history = []

def generate_response(user_input):
    """
    Create a handler that calls the Conversational agent
    and returns a response to be rendered in the UI
    """
    global chat_history

    # Add user input to chat history
    chat_history.append({"role": "user", "content": user_input})

    # Prepare the input for the agent executor
    input_data = {
        "input": user_input,
        "chat_history": chat_history
    }

    # Invoke the agent executor
    response = urbanism_agent_executor.invoke(input_data)

    # Add agent response to chat history
    chat_history.append({"role": "agent", "content": response['output']})

    return response['output']