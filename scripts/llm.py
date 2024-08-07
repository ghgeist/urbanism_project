import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

# Create the LLM
llm = ChatOpenAI(
    openai_api_key=st.secrets["openai"]["openai_api_key"],
    model=st.secrets["openai"]["openai_model"],
)

# Create the Embedding model
embeddings = OpenAIEmbeddings(
    openai_api_key=st.secrets["openai"]["openai_api_key"]
)