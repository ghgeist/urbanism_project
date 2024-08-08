# Enable tools for the postgres agent
postgres_tools = [
    Tool.from_function(
        name="Postgres SQL Query",
        description="For when you need to find the national walkability index of a city.",
        func=get_answer_by_sql_query
    ),
]

# Read the postgres template content from the file
try:
    with open(r'scripts\postgres_prompt_template.txt', 'r', encoding='utf-8') as file:
        postgres_template_content = file.read()
except FileNotFoundError:
    postgres_template_content = "Default postgres template content"  # Handle the case where the file is not found

# Create the PromptTemplate using the content from the file for postgres
postgres_agent_prompt = PromptTemplate.from_template(postgres_template_content)

# Create the postgres agent using the LLM, tools, and prompt template
postgres_agent = create_react_agent(llm, postgres_tools, postgres_agent_prompt)

# Create an AgentExecutor to manage the postgres agent and tools
postgres_agent_executor = AgentExecutor(
    agent=postgres_agent,
    tools=postgres_tools,
    verbose=True,
    handle_parsing_errors=True
)

# Initialize chat history
chat_history = []

# Function to generate a response from the chatbot
def generate_response(user_input, query_type):
    """
    Create a handler that calls the appropriate agent
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

        # Select the appropriate agent executor based on query type
        if query_type == "urbanism":
            response = urbanism_agent_executor.invoke(input_data)
        elif query_type == "postgres":
            response = postgres_agent_executor.invoke(input_data)
        else:
            raise ValueError("Invalid query type")

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