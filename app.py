import streamlit as st
import mysql.connector
import pandas as pd

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="hasa",
    database="redbus_db"
)

# Query data from MySQL
def get_data(query):
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [i[0] for i in cursor.description]
    cursor.close()
    return pd.DataFrame(rows, columns=columns)

# Filter options
st.title("Redbus Schedule")

# Define the filter options
bustype = st.selectbox("Select bustype", ["All", "AC", "Non-AC"])
price_range = st.slider("Price Range", 0, 5000, (100, 3000))
route = st.text_input("Enter Route")

# Construct SQL Query based on filters
query = "SELECT * FROM bus_routes WHERE 1=1"

if bustype != "All":
    query += f" AND bustype = '{bustype}'"

if route:
    query += f" AND (busname LIKE '%{route}%' OR bustype LIKE '%{route}%')"

query += f" AND price BETWEEN {price_range[0]} AND {price_range[1]}"

# Fetch and display the filtered data
df = get_data(query)
st.dataframe(df)

# Close the connection when done
conn.close()
