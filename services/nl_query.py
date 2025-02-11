import argparse
import os
import re  # Used to strip markdown code fences
import json  # For processing JSON prompt templates
from pathlib import Path  # To check file extensions
from dotenv import load_dotenv  # Load environment variables from a .env file
import openai
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.pool import SimpleConnectionPool
from openai import OpenAIError

# Load environment variables from .env file
load_dotenv()

# Database Connection Pool (adjust minconn/maxconn as needed)
DB_POOL = SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    dsn=os.getenv("NEONDB_URI")
)

def get_api_key(provided_api_key: str = None) -> str:
    """
    Returns the OpenAI API key from a provided parameter or from the environment.
    """
    if provided_api_key:
        return provided_api_key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OpenAI API key.")
    return api_key

def load_prompt_template(filepath: str) -> str:
    """
    Loads a prompt template from a file.
    Supports plain text and JSON formats.
    
    For JSON files, the JSON is expected to contain a "prompt" field and optionally an "examples" array.
    Each example in the array can have "name", "description" and "query" keys.
    """
    path = Path(filepath)
    if path.suffix.lower() == ".json":
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
        prompt = data.get("prompt", "")
        examples = data.get("examples", [])
        if examples:
            prompt += "\n\nExamples:\n"
            for ex in examples:
                name = ex.get("name", "")
                description = ex.get("description", "")
                query = ex.get("query", "")
                prompt += f"- {name}: {description}\n  SQL: {query}\n"
        return prompt
    else:
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()

def translate_nl_to_sql(client, nl_query: str, model: str = "gpt-4-turbo",
                         max_tokens: int = 150, temperature: float = 0) -> str:
    """
    Translates natural language to SQL using the prompt template
    """
    prompt_template = load_prompt_template("prompts\sql_prompt_examples.json")
    user_content = f"{prompt_template}\n\nQuery: {nl_query}"
    messages = [
        {
            "role": "system",
            "content": "You are a PostgreSQL SQL expert. Generate only valid SQL queries for PostgreSQL. Do not include any additional comments or explanations."
        },
        {"role": "user", "content": user_content}
    ]
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=[";"]  # Ensures single-query output
        )
        sql_query = response.choices[0].message.content.strip()
        # Remove markdown code block fences if present
        sql_query = re.sub(r"^```(?:sql)?\s*", "", sql_query)
        sql_query = re.sub(r"\s*```$", "", sql_query)
        return sql_query
    except OpenAIError as e:
        return f"Error generating SQL: {str(e)}"

def generate_sql_query(client, nl_query: str, model: str = "gpt-4-turbo",
                       max_tokens: int = 150, temperature: float = 0) -> str:
    """
    Generates a SQL query using an alternate prompt template from:
    """
    prompt_template = load_prompt_template("prompts\sql_prompt_examples.json")
    user_content = f"{prompt_template}\n\nQuery: {nl_query}"
    messages = [
        {
            "role": "system",
            "content": "You are a PostgreSQL SQL expert. Generate only valid SQL queries for PostgreSQL. Do not include any additional comments or explanations."
        },
        {"role": "user", "content": user_content}
    ]
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=[";"]
        )
        sql_query = response.choices[0].message.content.strip()
        sql_query = re.sub(r"^```(?:sql)?\s*", "", sql_query)
        sql_query = re.sub(r"\s*```$", "", sql_query)
        return sql_query
    except OpenAIError as e:
        return f"Error generating SQL: {str(e)}"

def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """
    Safely executes a SQL query on NeonDB and returns results as a DataFrame.
    """
    conn = None
    try:
        conn = DB_POOL.getconn()
        with conn.cursor() as cur:
            cur.execute(sql.SQL(sql_query))
            columns = [desc[0] for desc in cur.description]
            data = cur.fetchall()
        return pd.DataFrame(data, columns=columns)
    except psycopg2.Error as e:
        return pd.DataFrame({"error": [str(e)]})
    finally:
        if conn:
            DB_POOL.putconn(conn)

def generate_natural_language_summary(client, results: pd.DataFrame, model: str = "gpt-4-turbo",
                                      prompt_header: str = "Summarize the SQL query results in natural language:",
                                      max_tokens: int = 150, temperature: float = 0.7) -> str:
    """
    Generates a natural language summary of SQL query results using the provided OpenAI client.
    """
    if results.empty:
        return "No results found."
    results_str = results.to_string(index=False)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": f"{prompt_header}\n\n{results_str}"}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except OpenAIError as e:
        return f"Error generating summary: {str(e)}"

def process_nl_query(nl_query: str, provided_api_key: str = None, use_alternate: bool = False) -> str:
    """
    Full pipeline:
    - Initialize API client.
    - Translate NL to SQL using either the default or alternate prompt template.
    - Execute the SQL query.
    - Generate a natural language summary of the results.
    """
    api_key = get_api_key(provided_api_key)
    client = openai.OpenAI(api_key=api_key)
    if use_alternate:
        sql_query = generate_sql_query(client, nl_query)
    else:
        sql_query = translate_nl_to_sql(client, nl_query)
    if "Error generating SQL" in sql_query:
        return sql_query
    results = execute_sql_query(sql_query)
    if "error" in results.columns:
        return f"SQL Execution Error: {results['error'][0]}"
    return generate_natural_language_summary(client, results)

def main():
    parser = argparse.ArgumentParser(description="Process a natural language query.")
    parser.add_argument("query", type=str, help="The natural language query to process")
    parser.add_argument("--alternate", action="store_true", help="Use alternate SQL generation prompt")
    args = parser.parse_args()
    output = process_nl_query(args.query, use_alternate=args.alternate)
    print(output)

if __name__ == "__main__":
    main()
