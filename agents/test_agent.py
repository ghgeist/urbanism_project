import os
import streamlit as st
from langchain import hub
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.tools import Tool

# Set the OpenAI API key from Streamlit secrets
os.environ["OPENAI_API_KEY"] = st.secrets["openai"]["openai_api_key"]
model = st.secrets["openai"]["openai_model"]

# Create the ChatOpenAI instance 
prompt = hub.pull("hwchase17/react")
model =ChatOpenAI(model=model, temperature=0)\

basic_chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an urban planning expert providing information about cities."),
        ("human", "{input}"),
    ]
)

# Create the urbanism chat pipeline
basic_chat= basic_chat_prompt | model | StrOutputParser()

tools = [
    Tool.from_function(
        name="General Chat",
        description="For general urbanism chat not covered by other tools",
        func=basic_chat.invoke,
    )
]


agent = create_react_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

agent_executor.invoke({"input": "hi"})