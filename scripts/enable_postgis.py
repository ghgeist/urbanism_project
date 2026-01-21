"""
Enable PostGIS extension in Replit PostgreSQL database.
Run this script once before loading data into the database.
"""
import logging
import psycopg2
import os

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Get database connection details from Replit PostgreSQL environment variables
db_host = os.environ.get('PGHOST')
db_port = os.environ.get('PGPORT')
db_name = os.environ.get('PGDATABASE')
db_username = os.environ.get('PGUSER')
db_password = os.environ.get('PGPASSWORD')

if not all([db_host, db_port, db_name, db_username, db_password]):
    raise Exception("Could not find database credentials. Ensure Replit PostgreSQL is provisioned.")

try:
    logging.info("Connecting to PostgreSQL database...")
    logging.info(f"Host: {db_host}, Port: {db_port}, Database: {db_name}, User: {db_username}")
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
    
    # Verify PostGIS version
    cursor.execute("SELECT PostGIS_version();")
    postgis_version = cursor.fetchone()[0]
    logging.info(f"PostGIS version: {postgis_version}")
    
    cursor.close()
    connection.close()

except Exception as e:
    logging.error(f"Error: {e}")
    raise
