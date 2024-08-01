import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io

# Goal: Map the walkability scores by zip code
# To Do:
# Figure out how to speed up the API call for the walkability scores
# Figure out how to map the block data to zip codes. 
# Figure out how to visualize the data

#NatWalkInd ( type: esriFieldTypeDouble, alias: Walkability Index )
#GEOID20 ( type: esriFieldTypeString, alias: Census block group 12-digit FIPS code (2018), length: 50 )#



# Function to fetch data from the API
@st.cache_data
def fetch_data(api_url):
    response = requests.get(api_url)
    response.raise_for_status()  # Raise an error for bad status codes
    return response.content

# API URL
api_url = 'https://edg.epa.gov/EPADataCommons/public/OA/EPA_SmartLocationDatabase_V3_Jan_2021_Final.csv'

# Fetch the data
data_content = fetch_data(api_url)

# Load only necessary columns
columns_to_load = ['GEOID20', 'NatWalkInd']
dtype = {
    'GEOID20': 'string',
    'NatWalkInd': 'float64'
}
data = pd.read_csv(io.StringIO(data_content.decode('utf-8')), usecols=columns_to_load, dtype=dtype)

# Streamlit app
st.title("Walkability Scores Visualization")

# Display the data
st.write("### Walkability Scores Data", data.head())