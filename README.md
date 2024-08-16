<p align="center">
  <img src="assets\header_image.jpg"> 
</p>

# Exploring the National Walkability Index

# Project Overview
This project explores the National Walkability Index, a dataset developed by the U.S. Environmental Protection Agency (EPA) to measure the walkability of neighborhoods across the United States. The index ranges from 1 to 20, with higher values indicating greater walkability. The dataset includes the walkability index for each census block group in the United States, as well as the corresponding Federal Information Processing System (FIPS) code for each block group.

# Link to Web App
[Exploring the U.S. National Walkability Index](https://citybot.streamlit.app/)

# Installation and Setup

## Codes and Resources Used
- **Editor:** VSCode
- **Python Version:** 3.12
- **Database:** Neon PostgreSQL
- **Web App:** Streamlit

## Python Packages Used
- **Web App:**  streamlit
- **Data Manipulation:** geopandas, geopy, pandas, shapely, sqlalchemy 
- **Data Visualization:** folium, folium_static

# Data Preprocessing
- [compress_walkability_df.ipynb](https://github.com/ghgeist/urbanism_project/blob/main/notebooks/compress_walkability_df.ipynb)
  - Simplifies the geometry of the original walkability dataset
  - Drops rows that are not part of a CBSA
  - Tests to optimize column data types for postgres table creation
  - Estimates PostgreSQL table size

# Future Directions
* Enable Gen AI features with RAG to enable users to query the underlying data

# Data
## Data Sources
- [Walkability Index](https://catalog.data.gov/dataset/walkability-index3)
- [Federal Information Processing System (FIPS) Codes for States and Counties](https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt)
- [Smart Location Mapping](https://www.epa.gov/smartgrowth/smart-location-mapping#walkability)

# License
[MIT License](https://opensource.org/license/mit/)
