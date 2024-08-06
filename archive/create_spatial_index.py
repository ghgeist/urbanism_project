import os
import logging
import psycopg2
from dotenv import load_dotenv
from tqdm import tqdm
import time

# Load environment variables from .env file
load_dotenv()

# Configure logging to output to the terminal
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Get database connection details from environment variables
db_username = os.getenv('DB_USERNAME')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

try:
    logging.info("Creating connection to PostgreSQL database...")
    # Create a connection to the PostgreSQL database
    connection = psycopg2.connect(
        user=db_username,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name
    )
    cursor = connection.cursor()

    logging.info("Creating spatial index on the 'geometry' column...")
    
    # Simulate progress with a spinner
    with tqdm(total=100, desc="Creating Index", bar_format="{l_bar}{bar} [time left: {remaining}]") as pbar:
        for _ in range(10):
            time.sleep(0.1)  # Simulate work being done
            pbar.update(10)
    
    # Create spatial index on the 'geometry' column
    cursor.execute("CREATE INDEX IF NOT EXISTS geometry_idx ON national_walkability_index USING GIST (geometry);")
    connection.commit()

    logging.info("Spatial index created successfully.")

except Exception as e:
    logging.error("Error: %s", e)
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals():
        connection.close()
        logging.info("PostgreSQL connection is closed")