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
    try:
        with placeholder.container():
            # CPU SECTION
            cpu_res = requests.get(f"{API_BASE}/detect/live", timeout=5).json()
            if cpu_res['status'] == 'success':
                st.subheader("🚀 CPU Anomaly Detection")
                df_cpu = pd.DataFrame(cpu_res['all_metrics'])
                fig_cpu = go.Figure()
                fig_cpu.add_trace(go.Scatter(x=df_cpu['time_formatted'], y=df_cpu['value'], name='CPU Usage'))
                anoms = df_cpu[df_cpu['is_anomaly'] == -1]
                if not anoms.empty:
                    fig_cpu.add_trace(go.Scatter(x=anoms['time_formatted'], y=anoms['value'], mode='markers', name='Anomaly', marker=dict(color='red', size=10, symbol='x')))
                fig_cpu.update_layout(template="plotly_dark")
                st.plotly_chart(fig_cpu, use_container_width=True, key="cpu_chart_final")

            # MEMORY SECTION
            st.divider()
            st.subheader("🧠 Memory Forecast")
            mem_res = requests.get(f"{API_BASE}/predict/memory", timeout=10).json()
            if mem_res['status'] == 'success':
                f_df = pd.DataFrame(mem_res['forecast'])
                fig_mem = go.Figure()
                fig_mem.add_trace(go.Scatter(x=f_df['time_formatted'], y=f_df['yhat'], name='Trend', line=dict(color='#00ffcc', dash='dash')))
                if mem_res['predicted_val_2h_mb'] > (mem_res['current_val_mb'] * 1.2):
                    fig_mem.add_vline(x=f_df['time_formatted'].iloc[-1], line_width=3, line_dash="dash", line_color="orange")
                fig_mem.update_layout(template="plotly_dark")
                st.plotly_chart(fig_mem, use_container_width=True, key="mem_chart_final")

            # DISK SECTION
            st.divider()
            st.subheader("💾 Disk Capacity Trend")
            disk_res = requests.get(f"{API_BASE}/predict/disk", timeout=10).json()
            if disk_res['status'] == 'success':
                d_df = pd.DataFrame(disk_res['forecast'])
                fig_disk = go.Figure()
                fig_disk.add_trace(go.Scatter(x=d_df['ds'], y=d_df['yhat'], name='Usage', line=dict(color='#ffa500')))
                fig_disk.update_layout(template="plotly_dark", yaxis_range=[0, 100])
                st.plotly_chart(fig_disk, use_container_width=True, key="disk_chart_final")

    except Exception as e:
        st.info(f"Syncing... ({e})")
    time.sleep(15)
