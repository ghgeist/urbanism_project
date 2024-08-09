import ast
import json
import os
import re
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker
from geoalchemy2 import Geometry
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.agents.agent_toolkits import create_retriever_tool

load_dotenv()

# Set the OpenAI API key from Streamlit secrets
os.environ["OPENAI_API_KEY"] = st.secrets["openai"]["openai_api_key"]
model = st.secrets["openai"]["openai_model"]

# Read database connection details from Streamlit secrets
db_secrets = st.secrets["connections"]["postgresql"]
username = db_secrets["username"]
password = db_secrets["password"]
hostname = db_secrets["host"]
port_number = db_secrets["port"]
db_name = db_secrets["database"]

# Create the ChatOpenAI instance
llm = ChatOpenAI(model=model, temperature=0)

# Create the PostgreSQL URI
postgres_uri = f"postgresql+psycopg2://{username}:{password}@{hostname}:{port_number}/{db_name}"

# Create the SQLAlchemy engine
engine = create_engine(postgres_uri)

# Example of defining a table with a geometry column
Base = declarative_base()

class ExampleTable(Base):
    __tablename__ = 'example_table'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    geometry = Column(Geometry('POINT'))

# Create the table in the database
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Function to execute SQL queries
def execute_query(query):
    result = session.execute(text(query))
    return result.fetchall()

# Create an SQLDatabase instance from the URI
db = SQLDatabase.from_uri(postgres_uri)

# Set up the example selector
## Read the contents of the JSON file
sql_prompt_examples = 'prompts/sql_prompt_examples.json'

## Read the contents of the JSON file
with open(sql_prompt_examples, 'r', encoding='utf-8') as file:
    sql_prompt_examples = json.load(file)

## Create the example selector
example_selector = SemanticSimilarityExampleSelector.from_examples(
    sql_prompt_examples,
    OpenAIEmbeddings(),
    FAISS,
    k=5,
    input_keys=["input"],
)

# Create FewShotPromptTemplate
## Define the path to the Markdown file
system_prefix = 'prompts/system_prefix.md'

# Read the contents of the Markdown file
with open(system_prefix, 'r', encoding='utf-8') as file:
    system_prefix_content = file.read()

few_shot_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=PromptTemplate.from_template(
        "User input: {input}\nSQL query: {query}"
    ),
    input_variables=["input", "dialect", "top_k"],
    prefix=system_prefix,
    suffix="",
)

# Deal with the high-cardinatlity problem
## This code probably only has to be run once. Will clean this up later.
def query_as_list(db, query):
    res = db.run(query)
    res = [el for sub in ast.literal_eval(res) for el in sub if el]
    res = [re.sub(r"\b\d+\b", "", string).strip() for string in res]
    return list(set(res))

## Get the list of proper nouns
cbsa_names = query_as_list(db, "SELECT cbsa_name FROM national_walkability_index;")
csa_names = query_as_list(db, "SELECT csa_name FROM national_walkability_index;")

## Create the vector database from the lists of proper nouns
vector_db = FAISS.from_texts(cbsa_names + csa_names, OpenAIEmbeddings())

## Create the retriever tool
retriever = vector_db.as_retriever(search_kwargs={"k": 5})
description = """Use to look up values to filter on. Input is an approximate spelling of the proper noun, output is
valid proper nouns. Use the noun most similar to the search."""
retriever_tool = create_retriever_tool(
    retriever,
    name="search_proper_nouns",
    description=description,
)

# Create the chat prompt
full_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate(prompt=few_shot_prompt),  # System message with few-shot examples
        ("human", "{input}"),  # Placeholder for human input
        MessagesPlaceholder("agent_scratchpad"),  # Placeholder for agent's intermediate messages
    ]
)

# Create the agent
pg_agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    extra_tools=[retriever_tool],
    prompt=full_prompt,
    agent_type="openai-tools",
    verbose=True,
)

# # Use this code to test the agent
# pg_agent_executor.invoke(
#     "How many block groups are there in the Knoxville area?"
# )