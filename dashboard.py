import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px

st.set_page_config(page_title="AIOps Self-Healing Dashboard", layout="wide")

st.title("AIOps Real-Time Autonomous Healer")
st.write("Monitoring Kubernetes Cluster with Isolation Forest Anomaly Detection")

# Sidebar for Status
st.sidebar.header("System Status")
health = requests.get("http://localhost:8000/health").json()
st.sidebar.success("API: Online") if health['status'] == "ok" else st.sidebar.error("API: Offline")

# Placeholder for the graph
placeholder = st.empty()

while True:
    try:
        # Fetch data from your FastAPI detect/live endpoint
        response = requests.get("http://localhost:8000/detect/live").json()
        
        if response['status'] == 'success':
            # Create Dataframe from API response
            data = pd.DataFrame(response['anomalies']) # This would be the full metrics list
            # Note: We should update main.py to return ALL points, not just anomalies for the graph
            
            # (Logic for plotting both normal and anomaly points)
            fig = px.line(data, x='timestamp', y='value', title="Live CPU Utilization")
            # Highlight anomalies in red
            # fig.add_trace(...) 
            
            with placeholder.container():
                st.plotly_chart(fig, use_container_width=True)
                st.metric("Anomalies Detected", response['anomalies_detected'])
                
    except Exception as e:
        st.error(f"Dashboard Error: {e}")
    
    time.sleep(10)
