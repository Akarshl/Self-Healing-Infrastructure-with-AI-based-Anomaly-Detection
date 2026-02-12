import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time

# --- Page Configuration ---
st.set_page_config(page_title="AIOps Command Center", layout="wide")

st.title("🛡️ AIOps Autonomous Self-Healing Dashboard")
st.markdown("### Hybrid AI: Reactive Anomaly Detection & Predictive Forecasting")

API_BASE = "http://localhost:8000"

# --- Sidebar Infrastructure Status ---
st.sidebar.header("System Infrastructure")
try:
    health = requests.get(f"{API_BASE}/health", timeout=2).json()
    if health.get('status') == "ok":
        st.sidebar.success("✅ AIOps Brain: Online")
    else:
        st.sidebar.error("❌ AIOps Brain: Error")
except Exception:
    st.sidebar.error("❌ AIOps Brain: Offline")

placeholder = st.empty()

# --- Dashboard Refresh Loop ---
while True:
    with placeholder.container():
        # --- 1. CPU Section (Reactive Layer) ---
        try:
            cpu_res = requests.get(f"{API_BASE}/detect/live", timeout=5).json()
            if cpu_res['status'] == 'success':
                st.subheader("🚀 Reactive Layer: CPU Anomaly Detection")
                df_cpu = pd.DataFrame(cpu_res['all_metrics'])
                summary = cpu_res['summary']

                c1, c2, c3 = st.columns(3)
                c1.metric("Current CPU Load", f"{summary['current_usage']:.4f}")
                c2.metric("Anomalies (30m)", summary['anomalies_found'])
                c3.metric("Healer Status", "ACTING" if summary['anomalies_found'] > 0 else "IDLE")

                fig_cpu = go.Figure()
                fig_cpu.add_trace(go.Scatter(
                    x=df_cpu['time_formatted'], 
                    y=df_cpu['value'], 
                    name='CPU Usage',
                    line=dict(color='#1f77b4', width=2)
                ))

                anoms = df_cpu[df_cpu['is_anomaly'] == -1]
                if not anoms.empty:
                    fig_cpu.add_trace(go.Scatter(
                        x=anoms['time_formatted'], 
                        y=anoms['value'], 
                        mode='markers', 
                        name='Anomaly', 
                        marker=dict(color='red', size=10, symbol='x')
                    ))

                fig_cpu.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Usage Core",
                    template="plotly_dark",
                    height=400
                )
                st.plotly_chart(fig_cpu, use_container_width=True, key="cpu_chart_live")
        except Exception as e:
            st.warning(f"Connecting to CPU API... ({e})")

        # --- 2. Memory Section (Predictive Layer) ---
        st.divider()
        st.subheader("🧠 Memory Forecast (Prophet)")
        try:
            mem_res = requests.get(f"{API_BASE}/predict/memory", timeout=10).json()
            if mem_res['status'] == 'success':
                f_df = pd.DataFrame(mem_res['forecast'])
                st.write(f"Current: **{mem_res['current_val_mb']} MB** | Predicted (2h): **{mem_res['predicted_val_2h_mb']} MB**")

                fig_mem = go.Figure()
                # Main Trend Line (Forecasted yhat)
                fig_mem.add_trace(go.Scatter(
                    x=f_df['time_formatted'], 
                    y=f_df['yhat'], 
                    name='Predicted Trend', 
                    line=dict(color='#00ffcc', dash='dash')
                ))

                # Predictive Remediation Marker (Orange Triangle)
                # Triggers when predicted growth > 20%
                if mem_res['predicted_val_2h_mb'] > (mem_res['current_val_mb'] * 1.2):
                    fig_mem.add_trace(go.Scatter(
                        x=[f_df['time_formatted'].iloc[-1]],
                        y=[f_df['yhat'].iloc[-1]],
                        mode='markers+text',
                        name='RESTART TRIGGERED',
                        text=["RESTART"],
                        textposition="top center",
                        marker=dict(color='orange', size=12, symbol='triangle-up')
                    ))
                    st.warning("🔮 AIOps Insight: Memory Leak Trend Detected - Healer Action Triggered")

                fig_mem.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(fig_mem, use_container_width=True, key="mem_chart_forecast")
        except Exception:
            st.info("Calculating Memory Forecast...")

        # --- 3. Disk Section (Strategic Layer) ---
        st.divider()
        st.subheader("💾 Disk Capacity Trend")
        try:
            disk_res = requests.get(f"{API_BASE}/predict/disk", timeout=10).json()
            if disk_res['status'] == 'success':
                d_df = pd.DataFrame(disk_res['forecast'])
                d_df['time_short'] = pd.to_datetime(d_df['ds']).dt.strftime('%H:%M')

                st.write(f"Usage: **{disk_res['current_usage_percent']}%** | ETA 90%: **{disk_res['days_until_90_percent']}**")

                fig_disk = go.Figure()
                fig_disk.add_trace(go.Scatter(
                    x=d_df['time_short'], 
                    y=d_df['yhat'], 
                    name='Disk Usage Trend', 
                    line=dict(color='#ffa500')
                ))
                
                # Critical Threshold Line
                fig_disk.add_hline(y=90, line_dash="dot", line_color="red", annotation_text="90% Critical Limit")

                fig_disk.update_layout(
                    template="plotly_dark", 
                    yaxis_range=[0, 100],
                    height=400
                )
                st.plotly_chart(fig_disk, use_container_width=True, key="disk_chart_trend")
            else:
                st.error("Disk API returned no data. Check Prometheus metrics.")
        except Exception:
            st.info("Waiting for Disk Capacity metrics...")

    time.sleep(15)
