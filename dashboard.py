import streamlit as st
import sqlite3
import pandas as pd 
import time
import altair as alt

st.title("Smart Gas Guardian - Dashboard")

@st.fragment(run_every = "2s")
def show_data():
    conn = sqlite3.connect("readings.db")
    df = pd.read_sql_query("SELECT * FROM readings ORDER BY id DESC LIMIT 1000", conn)
    #df = df.sort_values("id")
    conn.close()
    ultima = df.iloc[0]
    if ultima["rule_alert"]==1:
        status = "ALERT"
    elif ultima["is_anomaly"]==1:
        status = "WARNING"
    else:
        status = "NORMAL"
    if status == "NORMAL":
        st.success("NORMAL")
    elif status == "WARNING":
        st.warning("WARNING")
    else:
        st.error("ALERT")
    st.metric("Current gas value", ultima["gas_value"])
    ultima_ora = pd.to_datetime(ultima["timestamp"])
    varsta = (pd.Timestamp.now()-ultima_ora).total_seconds()
    if(varsta>15):
        st.error(f"SENSOR OFFLINE - last reading {int(varsta)}s ago")
    else:
        st.caption(f"Sensor online - last reading {int(varsta)}s ago")
    st.dataframe(df)
    df_grafic = df.sort_values("timestamp")
    warning_df = df_grafic[df_grafic["is_anomaly"]==1]
    alert_df = df_grafic[df_grafic["rule_alert"]==1]
    linie = alt.Chart(df_grafic).mark_line().encode(x="timestamp:T", y=alt.Y("gas_value:Q", scale = alt.Scale(zero = False)))
    p_warning = alt.Chart(warning_df).mark_circle(color = "orange", size = 50).encode(x="timestamp:T", y="gas_value:Q")
    p_alert = alt.Chart(alert_df).mark_circle(color = "red", size = 70).encode(x="timestamp:T", y="gas_value:Q")
    st.altair_chart(linie + p_warning + p_alert, use_container_width = True)
show_data()