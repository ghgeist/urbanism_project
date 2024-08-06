import streamlit as st

# Initialize connection.
conn = st.connection("postgresql", type="sql")

# Perform query.
df = conn.query('SELECT * FROM national_walkability_index LIMIT 5', ttl="10m")

st.dataframe(df)