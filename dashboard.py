import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time

st.set_page_config(page_title="AIOps Command Center", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ AIOps Autonomous Self-Healing Dashboard")
st.markdown("### Hybrid AI: Reactive Anomaly Detection & Predictive Forecasting")

# Sidebar Status
st.sidebar.header("System Infrastructure")
API_BASE = "http://localhost:8000"

try:
    health = requests.get(f"{API_BASE}/health").json()
    if health['status'] == "ok":
        st.sidebar.success("✅ AIOps Brain: Online")
        st.sidebar.info(f"Prometheus: {'Connected' if health['prometheus_connected'] else 'Disconnected'}")
    else:
        st.sidebar.error("❌ AIOps Brain: Error")
except:
    st.sidebar.error("❌ AIOps Brain: Offline")

placeholder = st.empty()

while True:
    with placeholder.container():
        # --- 1. REACTIVE LAYER: CPU (Isolation Forest) ---
        st.subheader("🚀 Reactive Layer: CPU Anomaly Detection")
        try:
            cpu_res = requests.get(f"{API_BASE}/detect/live").json()
            if cpu_res['status'] == 'success':
                df_cpu = pd.DataFrame(cpu_res['all_metrics'])
                summary = cpu_res['summary']
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Current CPU Load", f"{summary['current_usage']:.4f}")
                m2.metric("Anomalies (30m)", summary['anomalies_found'])
                m3.metric("Healer Status", "ACTING" if summary['anomalies_found'] > 0 else "IDLE")

                fig_cpu = go.Figure()
                fig_cpu.add_trace(go.Scatter(x=df_cpu['time_formatted'], y=df_cpu['value'], mode='lines', name='CPU Usage', line=dict(color='#1f77b4')))
                
                anomalies = df_cpu[df_cpu['is_anomaly'] == -1]
                if not anomalies.empty:
                    fig_cpu.add_trace(go.Scatter(x=anomalies['time_formatted'], y=anomalies['value'], mode='markers', name='Anomaly Detected', marker=dict(color='red', size=10, symbol='x')))
                
                fig_cpu.update_layout(height=400, template="plotly_dark", margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_cpu, use_container_width=True)
        except Exception as e:
            st.error(f"CPU API Error: {e}")

        st.divider()

        # --- 2. PREDICTIVE LAYER: Memory & Disk (Prophet) ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("🧠 Memory Forecast (Prophet)")
            try:
                mem_res = requests.get(f"{API_BASE}/predict/memory").json()
                if mem_res['status'] == 'success':
                    f_df = pd.DataFrame(mem_res['forecast'])
                    
                    st.write(f"Current: **{mem_res['current_val_mb']} MB** | Predicted (2h): **{mem_res['predicted_val_2h_mb']} MB**")
                    
                    fig_mem = go.Figure()
                    # Confidence Interval
                    fig_mem.add_trace(go.Scatter(x=f_df['time_formatted'], y=f_df['yhat_upper'], fill=None, mode='lines', line_color='rgba(255,255,255,0)', showlegend=False))
                    fig_mem.add_trace(go.Scatter(x=f_df['time_formatted'], y=f_df['yhat_lower'], fill='tonexty', mode='lines', line_color='rgba(255,255,255,0.1)', name='Confidence Range'))
                    # Forecast
                    fig_mem.add_trace(go.Scatter(x=f_df['time_formatted'], y=f_df['yhat'], mode='lines', line=dict(color='#00ffcc', dash='dash'), name='Predicted Trend'))
                    
                    fig_mem.update_layout(height=350, template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_mem, use_container_width=True)
            except: st.info("Calculating Memory Forecast...")

        with col_right:
            st.subheader("💾 Disk Capacity Trend")
            try:
                disk_res = requests.get(f"{API_BASE}/predict/disk").json()
                if disk_res['status'] == 'success':
                    d_df = pd.DataFrame(disk_res['forecast'])
                    d_df['ds'] = pd.to_datetime(d_df['ds']).dt.strftime('%H:%M')
                    
                    st.write(f"Current Usage: **{disk_res['current_usage_percent']}%**")
                    st.write(f"Time to 90%: **{disk_res['days_until_90_percent']}**")
                    
                    fig_disk = go.Figure()
                    fig_disk.add_trace(go.Scatter(x=d_df['ds'], y=d_df['yhat'], mode='lines', line=dict(color='#ffa500'), name='Disk Trend'))
                    # Threshold line
                    fig_disk.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="90% Limit")
                    
                    fig_disk.update_layout(height=350, template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20), yaxis_range=[0, 100])
                    st.plotly_chart(fig_disk, use_container_width=True)
            except: st.info("Calculating Disk Forecast...")

    time.sleep(15) # Refreshed every 15 seconds to allow Prophet to compute
