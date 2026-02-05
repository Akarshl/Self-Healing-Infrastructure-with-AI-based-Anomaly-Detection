import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time

st.set_page_config(page_title="AIOps Command Center", layout="wide")

st.title("🛡️ AIOps Autonomous Self-Healing Dashboard")
st.markdown("### Real-Time Anomaly Detection & Kubernetes Remediation")

# Sidebar Status
st.sidebar.header("System Infrastructure")
try:
    health = requests.get("http://localhost:8000/health").json()
    if health['status'] == "ok":
        st.sidebar.success("✅ AIOps Brain: Online")
    else:
        st.sidebar.error("❌ AIOps Brain: Error")
except:
    st.sidebar.error("❌ AIOps Brain: Offline")

# Dashboard Layout
col1, col2, col3 = st.columns(3)
placeholder = st.empty()

while True:
    try:
        response = requests.get("http://localhost:8000/detect/live").json()
        
        if response['status'] == 'success':
            df = pd.DataFrame(response['all_metrics'])
            summary = response['summary']
            
            with placeholder.container():
                # Top Level Metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Current CPU Load", f"{summary['current_usage']:.2f}")
                col2.metric("Anomalies in Windows", summary['anomalies_found'])
                col3.metric("Healing Status", "Active" if summary['anomalies_found'] > 0 else "Monitoring")

                # Visualization
                fig = go.Figure()

                # Normal Line
                fig.add_trace(go.Scatter(
                    x=df['time_formatted'], y=df['value'],
                    mode='lines', name='CPU Usage',
                    line=dict(color='#1f77b4', width=2)
                ))

                # Anomaly Markers
                anomalies = df[df['is_anomaly'] == -1]
                if not anomalies.empty:
                    fig.add_trace(go.Scatter(
                        x=anomalies['time_formatted'], y=anomalies['value'],
                        mode='markers', name='Anomaly Detected',
                        marker=dict(color='red', size=10, symbol='x')
                    ))

                fig.update_layout(
                    title="Real-Time Isolation Forest Inference",
                    xaxis_title="Time",
                    yaxis_title="CPU Core Usage",
                    template="plotly_dark",
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Raw Data Preview
                if st.checkbox("Show Raw Data Logs"):
                    st.write(df.tail(10))

    except Exception as e:
        st.warning(f"Waiting for data from API... ({e})")
    
    time.sleep(10)
