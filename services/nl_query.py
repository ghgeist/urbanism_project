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
import logging
import atexit

# Load environment variables from .env file
load_dotenv()

# Database Connection Pool (adjust minconn/maxconn as needed)
DB_POOL = SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    dsn=os.getenv("NEONDB_URI")
)

# Add these constants at the top with other globals
DEFAULT_MODEL = "gpt-4-turbo"
DEFAULT_SQL_MAX_TOKENS = 150
DEFAULT_SQL_TEMPERATURE = 0.1
DEFAULT_SUMMARY_MAX_TOKENS = 150
DEFAULT_SUMMARY_TEMPERATURE = 0.7

# At the top of the file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def load_system_prompt(filepath: str) -> str:
    """
    Loads the system prompt instructions from a file.
    This file should contain only the instructions that are sent as the system message.
    """
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read()

def load_examples(filepath: str) -> str:
    """
    Loads and formats example SQL queries from a JSON file.

    The JSON file must be a list of dictionaries. Each dictionary should include:
      - "input": The natural language example.
      - "query": The corresponding SQL query.
      - "answer": (Optional) The expected answer or explanation.

    Returns:
        A formatted string aggregating all the examples.
    """
    with open(filepath, "r", encoding="utf-8") as file:
        examples = json.load(file)

    if not isinstance(examples, list):
        raise ValueError("Expected a JSON list of example dictionaries.")

    formatted_lines = ["Examples:"]
    for ex in examples:
        input_example = ex.get("input", "N/A")
        query_example = ex.get("query", "N/A")
        answer = ex.get("answer", "")
        display = f"- Input: {input_example}\n  SQL: {query_example}"
        if answer:
            display += f"\n  Answer: {answer}"
        formatted_lines.append(display)
        
    return "\n".join(formatted_lines)

def translate_nl_to_sql(client, nl_query: str, model: str = DEFAULT_MODEL,
                         max_tokens: int = DEFAULT_SQL_MAX_TOKENS, 
                         temperature: float = DEFAULT_SQL_TEMPERATURE) -> str:
    """
    Translates natural language to SQL using a separated system prompt file.
    """
    try:
        # Add input validation
        if not nl_query or not nl_query.strip():
            return "ERROR: Empty query provided"
        if not isinstance(nl_query, str):
            return "ERROR: Query must be a string"
            
        # Load a plain text file containing the system instructions.
        system_prompt = load_system_prompt("prompts/sql_prompt_instructions.txt")
        
        # Load and append examples if they exist
        try:
            examples = load_examples("prompts/sql_examples.json")
            system_prompt = f"{system_prompt}\n\n{examples}"
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # Continue without examples if file doesn't exist or is invalid
            
        user_content = f"Query: {nl_query}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=[";"],  # Ensures a single-query output
            presence_penalty=0.1,
            frequency_penalty=0.1
        )
        sql_query = response.choices[0].message.content.strip()
        # Remove markdown code block fences if present
        sql_query = re.sub(r"^```(?:sql)?\s*", "", sql_query)
        sql_query = re.sub(r"\s*```$", "", sql_query)
        
        if sql_query.startswith("ERROR:"):
            return f"Error generating SQL: {sql_query[7:]}"
        return sql_query
    except OpenAIError as e:
        return f"Error generating SQL: OpenAI API error - {str(e)}"
    except Exception as e:
        return f"Error generating SQL: Unexpected error - {str(e)}"

def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """
    Safely executes a SQL query on NeonDB and returns results as a DataFrame.
    """
    conn = None
    try:
        # Add basic SQL injection prevention
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'UPDATE', 'INSERT']
        if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
            return pd.DataFrame({"error": ["Potentially dangerous SQL operation detected"]})
            
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

def generate_natural_language_summary(client, results: pd.DataFrame, 
                                    model: str = DEFAULT_MODEL,
                                    max_tokens: int = DEFAULT_SUMMARY_MAX_TOKENS,
                                    temperature: float = DEFAULT_SUMMARY_TEMPERATURE) -> str:
    """
    Generates a natural language summary of SQL query results using the provided OpenAI client.
    """
    if results.empty:
        return "No results found."
    results_str = results.to_string(index=False)
    try:
        messages = [
            {
                "role": "system",
                "content": """You are a data analyst that explains query results in natural language.
                                Requirements:
                                - Provide a clear, concise summary of the data
                                - Highlight key insights and patterns
                                - Use proper grammar and professional tone
                                - If no meaningful insights exist, state that clearly
                                - Keep the summary focused and relevant"""
                                },
            {
                "role": "user", 
                "content": f"Summarize these SQL query results in natural language:\n\n{results_str}"
            }
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            presence_penalty=0.2,
            frequency_penalty=0.2
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except OpenAIError as e:
        return f"Error generating summary: {str(e)}"

def process_nl_query(nl_query: str, provided_api_key: str = None, use_alternate: bool = False) -> str:
    """
    Full pipeline for processing natural language queries.
    """
    try:
        logger.info(f"Processing query: {nl_query}")
        api_key = get_api_key(provided_api_key)
        client = openai.OpenAI(api_key=api_key)
        
        logger.info("Translating to SQL")
        sql_query = translate_nl_to_sql(client, nl_query)
        if "Error generating SQL" in sql_query:
            logger.error(f"SQL generation failed: {sql_query}")
            return sql_query
            
        logger.info(f"Executing SQL: {sql_query}")
        results = execute_sql_query(sql_query)
        if "error" in results.columns:
            logger.error(f"SQL execution failed: {results['error'][0]}")
            return f"SQL Execution Error: {results['error'][0]}"
            
        logger.info("Generating summary")
        return generate_natural_language_summary(client, results)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return f"Processing Error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Process a natural language query.")
    parser.add_argument("query", type=str, help="The natural language query to process")
    parser.add_argument("--alternate", action="store_true", help="Use alternate SQL generation prompt")
    args = parser.parse_args()
    output = process_nl_query(args.query, use_alternate=args.alternate)
    print(output)

# After DB_POOL initialization
def cleanup_connections():
    """Ensure all database connections are properly closed."""
    if DB_POOL:
        logger.info("Closing all database connections")
        DB_POOL.closeall()

atexit.register(cleanup_connections)

if __name__ == "__main__":
    main()
