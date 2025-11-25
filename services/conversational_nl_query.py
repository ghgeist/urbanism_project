from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool 
from nl_query import process_nl_query

# Use the new decorator for tools
@tool
def query_data(query: str) -> str:
    """
    Wraps the process_nl_query function so that LangChain can call it as a tool.
    """
    # You can add additional exception handling or logging as needed
    return process_nl_query(query)


# Initialize the language model with your desired parameters
llm = ChatOpenAI(temperature=0.3, model_name="gpt-4-turbo")

# Set up conversation memory to keep track of the chat history
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True) # return_messages=True is important for ChatPromptTemplate

# Define the prompt template for the agent
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """You are a helpful assistant expert in answering questions about the database. 
        Always use the query_data tool when you need to fetch information from the database.
        If you don't get the information you need, try rephrasing the query."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Create the agent using the OpenAI Functions agent type
agent = create_openai_functions_agent(llm, [query_data], prompt)

# Initialize the agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=[query_data], 
    memory=memory, 
    verbose=True
)


if __name__ == "__main__":
    print("Conversational Data Agent. Type 'exit' or 'quit' to stop.")
    while True:
        user_input = input("Your question: ")
        if user_input.lower() in ("exit", "quit"):
            break
        response = agent_executor.invoke({"input": user_input})
        print("Response:", response['output'])