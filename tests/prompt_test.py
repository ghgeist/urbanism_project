# Example data to substitute into the template
tools = "search, calculator"
tool_names = "search, calculator"
chat_history = "User: What are some notable buildings in Knoxville? AI: The Tennessee Theatre is one example."
input_data = "What about modern architecture?"
agent_scratchpad = "AI is analyzing modern buildings in Knoxville."

# Read the template content
try:
    with open(r'prompts/urbanism_prompt.txt', 'r', encoding='utf-8') as file:
        template_content = file.read()
except FileNotFoundError:
    print("The template file was not found.")
    exit(1)
except IOError:
    print("An error occurred while reading the template file.")
    exit(1)

# Format the template using str.format
try:
    final_prompt = template_content.format(
        tools=tools,
        tool_names=tool_names,
        chat_history=chat_history,
        input=input_data,
        agent_scratchpad=agent_scratchpad
    )
    print(final_prompt)
except KeyError as e:
    print(f"Missing placeholder: {e}")