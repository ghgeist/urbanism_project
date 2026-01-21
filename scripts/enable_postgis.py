"""
Enable PostGIS extension in Replit PostgreSQL database.
Run this script once before loading data into the database.
"""
import logging
import psycopg2
import os

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Get database connection details - try Replit PostgreSQL first, fallback to Streamlit secrets
db_host = os.environ.get('REPLIT_POSTGRES_HOST')
db_port = os.environ.get('REPLIT_POSTGRES_PORT')
db_name = os.environ.get('REPLIT_POSTGRES_DATABASE')
db_username = os.environ.get('REPLIT_POSTGRES_USER')
db_password = os.environ.get('REPLIT_POSTGRES_PASSWORD')

if not all([db_host, db_port, db_name, db_username, db_password]):
    # Fallback to Streamlit secrets
    try:
        import streamlit as st
        db_secrets = st.secrets["connections"]["postgresql"]
        db_username = db_secrets["username"]
        db_password = db_secrets["password"]
        db_host = db_secrets["host"]
        db_port = db_secrets["port"]
        db_name = db_secrets["database"]
    except Exception as e:
        raise Exception(f"Could not find database credentials. Set Replit PostgreSQL env vars or Streamlit secrets. Error: {e}")

try:
    logging.info("Connecting to PostgreSQL database...")
    connection = psycopg2.connect(
        user=db_username,
        password=db_password,
        host=db_host,
        port=int(db_port) if isinstance(db_port, str) else db_port,
        database=db_name
    )
    cursor = connection.cursor()

    logging.info("Enabling PostGIS extension...")
    cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    connection.commit()

    logging.info("PostGIS extension enabled successfully!")
    
    cursor.close()
    connection.close()

except Exception as e:
    logging.error(f"Error: {e}")
    raise
