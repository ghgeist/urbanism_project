from scripts.llm import llm
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema import StrOutputParser
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool

## Define the chat prompt template for urbanism
urbanism_chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an urban planning expert providing information about cities."),
        ("human", "{input}"),
    ]
)

## Create the urbanism chat pipeline
urbanism_chat = urbanism_chat_prompt | llm | StrOutputParser()

urbanism_tools = [
    Tool.from_function(
        name="General Chat",
        description="For general urbanism chat not covered by other tools",
        func=urbanism_chat.invoke,
    )
]

## Read the urbanism template content from the Markdown file
try:
    with open(r'prompts\urbanism_prompt.md', 'r', encoding='utf-8') as file:
        urbanism_template_content = file.read()
except FileNotFoundError:
    urbanism_template_content = "Default urbanism template content"  # Handle the case where the file is not found
    
## Create the PromptTemplate using the content from the file for urbanism
urbanism_agent_prompt = PromptTemplate.from_template(urbanism_template_content)

## Create the urbanism agent using the LLM and prompt template
urbanism_agent = create_react_agent(llm, prompt=urbanism_agent_prompt, tools=urbanism_tools)

## Create an AgentExecutor to manage the urbanism agent
urbanism_agent_executor = AgentExecutor(
    agent=urbanism_agent,
    tools=urbanism_tools,  # Pass the tools to the AgentExecutor
    verbose=True,
    handle_parsing_errors=True
)