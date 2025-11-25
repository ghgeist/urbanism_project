<p align="center">
  <img src="assets/header_image.jpg" alt="National Walkability Index" width="600"/>
</p>

# Exploring the National Walkability Index

## Project Overview
This project explores and analyzes the National Walkability Index—a dataset developed by the U.S. Environmental Protection Agency (EPA) that measures the walkability of neighborhoods across the United States. The index ranges from 1 to 20, with higher scores indicating greater walkability. Our goal is to provide insights through interactive visualizations and data analysis.

## Live Web Application
Experience the interactive analysis on our Streamlit web application:  
[Visit the Web App](https://urbanismproject.streamlit.app/)

## Table of Contents
- [Installation and Setup](#installation-and-setup)
- [Key Technologies and Resources](#key-technologies-and-resources)
- [Data Preprocessing](#data-preprocessing)
- [Data Sources](#data-sources)
- [Future Directions](#future-directions)
- [License](#license)

## Installation and Setup

### Prerequisites
- **Python:** Version 3.12 or newer
- **Database:** Neon PostgreSQL

### How to Run
1. **Clone the repository**
   ```bash
   git clone https://github.com/ghgeist/urbanism_project.git
   cd urbanism_project
   ```
2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Start the Web Application**
   ```bash
   streamlit run app.py
   ```

## Key Technologies and Resources
- **Editor:** Cursor
- **Programming Language:** Python 3.12
- **Database:** Neon PostgreSQL
- **Web Framework:** Streamlit

### Python Packages
- **Web App:** streamlit  
- **Data Manipulation & Spatial Analysis:** geopandas, geopy, pandas, shapely, sqlalchemy  
- **Data Visualization:** folium, folium_static

## Data Preprocessing
Data preprocessing is performed in the [compress_walkability_df.ipynb](https://github.com/ghgeist/urbanism_project/blob/main/notebooks/compress_walkability_df.ipynb) notebook, which includes:
- Simplification of geometry from the original dataset.
- Filtering out rows not part of a Core-Based Statistical Area (CBSA).
- Optimizing column data types for PostgreSQL table creation.
- Estimating the PostgreSQL table size.

## Data Sources
- [Walkability Index](https://catalog.data.gov/dataset/walkability-index3)
- [FIPS Codes for States and Counties](https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt)
- [Smart Location Mapping](https://www.epa.gov/smartgrowth/smart-location-mapping#walkability)

## Future Directions
We plan to enhance the project by integrating Gen AI features with Retrieval-Augmented Generation (RAG), enabling users to interactively query the underlying data.

## License
This project is licensed under the [MIT License](https://opensource.org/license/mit/).
