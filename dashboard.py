import streamlit as st
import sqlite3
import pandas as pd 
import time

st.title("Smart Gas Guardian - Dashboard")

@st.fragment(run_every = "2s")
def show_data():
    conn = sqlite3.connect("readings.db")
    df = pd.read_sql_query("SELECT * FROM readings ORDER BY id DESC LIMIT 300", conn)
    #df = df.sort_values("id")
    conn.close()

    st.dataframe(df)
    st.line_chart(df, x = "timestamp", y = "gas_value") # GRAFIC
show_data()