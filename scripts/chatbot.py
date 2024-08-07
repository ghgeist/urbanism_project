import asyncio
from collections import deque
from llm import llm
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema import StrOutputParser
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from tools.query_postgres import get_answer_by_sql_query
from langchain_core.runnables import RunnableWithMessageHistory

# Define the chat prompt template
chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an urban planning expert providing information about cities."),
        ("human", "{input}"),
    ]
)

# Create the urbanism chat pipeline
urbanism_chat = chat_prompt | llm | StrOutputParser()

# Define the asynchronous function separately
async def urbanism_chat_invoke(input):
    return await urbanism_chat.invoke(input)

# Enable tools for the chatbot
tools = [
    Tool.from_function(
        name="Urbanism Chat",
        description="For general urban planning and city development queries.",
        func=urbanism_chat_invoke,
    ),
    Tool.from_function(
        name="National Walkability Index Search",
        description="For when you need to find the walkability index of a city.",
        func=get_answer_by_sql_query
    ),
]

# Read the template content from the file
try:
    with open(r'scripts\urbanism_prompt_template.txt', 'r', encoding='utf-8') as file:
        template_content = file.read()
except FileNotFoundError:
    template_content = "Default template content"  # Handle the case where the file is not found
        
# Create the PromptTemplate using the content from the file
agent_prompt = PromptTemplate.from_template(template_content)

# Create the agent using the LLM, tools, and prompt template
agent = create_react_agent(llm, tools, agent_prompt)

# Create an AgentExecutor to manage the agent and tools
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)

# Initialize chat history
chat_history = []

# Function to generate a response from the chatbot
async def generate_response(user_input):
    """
    Create a handler that calls the Conversational agent
    and returns a response to be rendered in the UI
    """
    global chat_history
    try:
        # Prepare the input with chat history
        input_data = {
            "input": user_input,
            "chat_history": chat_history,
            "agent_scratchpad": ""
        }

        # Call the agent_executor's invoke method with the input data
        response = agent_executor.invoke(input_data)  # Removed await

        # Update chat history with user input and agent response
        chat_history.append({"role": "human", "content": user_input})
        if isinstance(response, str):
            chat_history.append({"role": "agent", "content": response})
            return response
        elif isinstance(response, dict) and 'output' in response:
            chat_history.append({"role": "agent", "content": response['output']})
            return response['output']
        else:
            raise ValueError("Unexpected response format")
    except Exception as ex:
        return f"An error occurred: {str(ex)}"