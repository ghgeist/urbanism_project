import os
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema import StrOutputParser
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

# Set the OpenAI API key from Streamlit secrets
os.environ["OPENAI_API_KEY"] = st.secrets["openai"]["openai_api_key"]
model = st.secrets["openai"]["openai_model"]

# Create the ChatOpenAI instance
llm = ChatOpenAI(model=model, temperature=0)

# Define the chat prompt template for urbanism
urbanism_chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an urban planning expert providing information about cities."),
        ("human", "{input}"),
    ]
)

# Create the urbanism chat pipeline
urbanism_chat = urbanism_chat_prompt | llm | StrOutputParser()

# Create the tools to be used by the urbanism agent
urbanism_tools = [
    Tool.from_function(
        name="General Chat",
        description="For general urbanism chat not covered by other tools",
        func=urbanism_chat.invoke,
    )
]

# Read the urbanism template
## GG 8/9/24: The template is missing Previous conversation history:{chat_history}. 
## This might be an issue that appears in the future
try:
    with open(r'prompts/urbanism_prompt.txt', 'r', encoding='utf-8') as file:
        urbanism_template_content = file.read()
except FileNotFoundError:
    urbanism_template_content = "Default urbanism template content"

# Create the PromptTemplate using the content from the file for urbanism
urbanism_agent_prompt = PromptTemplate.from_template(urbanism_template_content)

# # Create the urbanism agent using the LLM and prompt template
urbanism_agent = create_react_agent(llm, tools=urbanism_tools, prompt=urbanism_agent_prompt)

# Create an AgentExecutor to manage the urbanism agent
urbanism_agent_executor = AgentExecutor(
    agent=urbanism_agent,
    tools=urbanism_tools,
    verbose=True
)

# Use this code to test the agent
# urbanism_agent_executor.invoke({"input": "What are some cool buildings in Knoxville, Tennessee?"})