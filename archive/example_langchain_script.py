# This is a simple example of calling an LLM with LangChain.
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

def basic_chain():
    prompt = ChatPromptTemplate.from_template("Tell me the most noteworthy books by the author {author}")
    model = ChatOpenAI(model="gpt-4", api_key=openai_api_key)
    output_parser = StrOutputParser()

    chain = prompt | model | output_parser

    results = chain.invoke({"author": "William Faulkner"})
    print(results)

def main():
    basic_chain()

if __name__ == '__main__':
    main()