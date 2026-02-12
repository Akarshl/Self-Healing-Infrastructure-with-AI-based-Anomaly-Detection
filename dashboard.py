import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time

st.set_page_config(page_title="AIOps Command Center", layout="wide")
st.title("🛡️ AIOps Autonomous Self-Healing Dashboard")

API_BASE = "http://localhost:8000"
placeholder = st.empty()

while True:
    with placeholder.container():
        # --- 1. CPU SECTION ---
        try:
            cpu_res = requests.get(f"{API_BASE}/detect/live", timeout=10).json()
            if cpu_res['status'] == 'success':
                st.subheader("🚀 CPU Anomaly Detection")
                df_cpu = pd.DataFrame(cpu_res['all_metrics'])
                fig_cpu = go.Figure()
                fig_cpu.add_trace(go.Scatter(x=df_cpu['time_formatted'], y=df_cpu['value'], name='CPU Usage'))
                anoms = df_cpu[df_cpu['is_anomaly'] == -1]
                if not anoms.empty:
                    fig_cpu.add_trace(go.Scatter(x=anoms['time_formatted'], y=anoms['value'], mode='markers', name='Anomaly', marker=dict(color='red', size=10, symbol='x')))
                fig_cpu.update_layout(template="plotly_dark")
                st.plotly_chart(fig_cpu, width='stretch', key="cpu_viz_v3")
        except: st.warning("Connecting to CPU API...")

        # --- 2. MEMORY SECTION ---
        st.divider()
        st.subheader("🧠 Memory Forecast")
        try:
            mem_res = requests.get(f"{API_BASE}/predict/memory", timeout=20).json()
            if mem_res['status'] == 'success':
                f_df = pd.DataFrame(mem_res['forecast'])
                fig_mem = go.Figure()
                fig_mem.add_trace(go.Scatter(x=f_df['time_formatted'], y=f_df['yhat'], name='Forecast', line=dict(color='yellow', dash='dash')))
                if mem_res['predicted_val_2h_mb'] > (mem_res['current_val_mb'] * 1.2):
                    fig_mem.add_trace(go.Scatter(x=[f_df['time_formatted'].iloc[-1]], y=[f_df['yhat'].iloc[-1]], mode='markers+text', text=["RESTART"], name="Restart Marker", marker=dict(color='orange', size=12, symbol='triangle-up')))
                fig_mem.update_layout(template="plotly_dark")
                st.plotly_chart(fig_mem, width='stretch', key="mem_viz_v3")
        except: st.info("Calculating Memory Forecast...")

        # --- 3. DISK SECTION ---
        st.divider()
        st.subheader("💾 Disk Capacity Trend")
        try:
            disk_res = requests.get(f"{API_BASE}/predict/disk", timeout=20).json()
            if disk_res['status'] == 'success':
                d_df = pd.DataFrame(disk_res['forecast'])
                d_df['time_fmt'] = pd.to_datetime(d_df['ds']).dt.strftime('%H:%M')
                fig_disk = go.Figure()
                fig_disk.add_trace(go.Scatter(x=d_df['time_fmt'], y=d_df['yhat'], name='Usage Forecast', line=dict(color='yellow', dash='dash')))
                # SHOW CLEANUP MARKER: Logic matches healer.py
                if disk_res['current_usage_percent'] > 70:
                    fig_disk.add_trace(go.Scatter(x=[d_df['time_fmt'].iloc[-1]], y=[d_df['yhat'].iloc[-1]], mode='markers+text', text=["CLEANUP"], name="Cleanup Marker", marker=dict(color='orange', size=12, symbol='triangle-up')))
                fig_disk.update_layout(template="plotly_dark", yaxis_range=[0, 100])
                st.plotly_chart(fig_disk, width='stretch', key="disk_viz_v3")
        except: st.info("Establishing Disk Trend...")

    time.sleep(20)
