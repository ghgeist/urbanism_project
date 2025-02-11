import os
import openai
import pandas as pd

# TODO: Here I want to make sure that the user can query the underlying database in natural language.
# I want to make sure that this script is following best practices for this process.

def get_api_key(provided_api_key: str = None) -> str:
    """
    Returns the API key from the provided parameter or from the environment.
    """
    if provided_api_key:
        return provided_api_key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key is missing. Please provide it or set it in the environment.")
    return api_key

def translate_nl_to_sql(
    nl_query: str,
    api_key: str,
    model: str = "gpt-3.5-turbo",
    prompt_header: str = "Translate the following natural language query to SQL. Only output the SQL query with no additional commentary.",
    max_tokens: int = 150,
    temperature: float = 0,
    stop: list = None
) -> str:
    """
    Translates a natural language query to SQL using a specified model and prompt.
    """
    if stop is None:
        stop = ["\n"]
    openai.api_key = api_key

    # Create messages including a system message that instructs the model to not hallucinate
    messages = [
        {"role": "system", "content": "You are a SQL assistant. Generate only valid SQL based on the provided natural language query. Do not add any extra commentary or speculation."},
        {"role": "user", "content": f"{prompt_header}\n\nQuery: {nl_query}"}
    ]

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=1,
        n=1,
        stop=stop
    )
    sql_query = response["choices"][0]["message"]["content"].strip()
    return sql_query

def execute_sql_query(sql_query: str, conn) -> pd.DataFrame:
    """
    Executes the provided SQL query using a database connection and returns the results as a DataFrame.
    """
    results = pd.read_sql_query(sql_query, conn)
    return results

def generate_natural_language_summary(
    results: pd.DataFrame,
    api_key: str,
    engine: str = "text-davinci-003",
    prompt_header: str = "Please summarize the following SQL query results in natural language. Use only information from the data provided and do not introduce any unverified details:",
    max_tokens: int = 150,
    temperature: float = 0.7
) -> str:
    """
    Generates a natural language summary from SQL query results using the specified engine and prompt.
    """
    results_str = results.to_string()
    prompt = f"{prompt_header}\n\n{results_str}"
    
    openai.api_key = api_key
    response = openai.Completion.create(
        engine=engine,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )
    summary = response.choices[0].text.strip()
    return summary

def process_nl_query(
    nl_query: str,
    conn,
    provided_api_key: str = None,
    query_model: str = "gpt-3.5-turbo",
    query_prompt: str = "Translate the following natural language query to SQL. Only output the SQL query.",
    query_max_tokens: int = 150,
    query_temperature: float = 0,
    summarization_engine: str = "text-davinci-003",
    summarization_prompt: str = "Please summarize the following SQL query results in natural language. Use only the provided data:",
    summarization_max_tokens: int = 150,
    summarization_temperature: float = 0.7
) -> str:
    """
    End-to-end processing:
      1. Translates a natural language query to SQL.
      2. Executes the SQL query.
      3. Generates and returns a natural language summary of the results.
      
    The parameters for query_model, summarization_engine, and the associated prompts can be controlled via the UI.
    """
    api_key = get_api_key(provided_api_key)
    sql_query = translate_nl_to_sql(
        nl_query, 
        api_key,
        model=query_model,
        prompt_header=query_prompt,
        max_tokens=query_max_tokens,
        temperature=query_temperature
    )
    results = execute_sql_query(sql_query, conn)
    nl_summary = generate_natural_language_summary(
        results,
        api_key,
        engine=summarization_engine,
        prompt_header=summarization_prompt,
        max_tokens=summarization_max_tokens,
        temperature=summarization_temperature
    )
    return nl_summary