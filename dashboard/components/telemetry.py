"""Telemetry Analysis: speed, throttle, brake, gear, and the circuit track map."""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from services import fastf1_service as ff1


def render(session, driver_code: str):
    driver_name = ff1.full_name(session, driver_code)
    st.subheader(f"Telemetry Analysis: {driver_name}")

    try:
        tel = ff1.get_fastest_lap_telemetry(session, driver_code)
        pos = ff1.get_position_telemetry(session, driver_code)
    except Exception:
        st.warning(
            "Telemetry data isn't available for this session right now. "
            "Lap times, standings, tyre and pit stop pages don't need telemetry "
            "and should still work normally. Try reloading the session from the top bar."
        )
        return

    st.markdown("#### Circuit Map: Fastest Lap Line, Coloured by Speed")
    speed_for_pos = (
        tel["Speed"].reindex(range(len(pos)))
        .ffill()
        .bfill()
        .fillna(tel["Speed"].mean())
    )
    map_fig = go.Figure(go.Scatter(
        x=pos["X"], y=pos["Y"], mode="markers+lines",
        marker=dict(size=4, color=speed_for_pos, colorscale="Turbo",
                    showscale=True, colorbar=dict(title="km/h")),
        line=dict(width=1, color="rgba(255,255,255,0.15)"),
    ))
    map_fig.update_layout(template="plotly_dark", height=500,
                           xaxis_visible=False, yaxis_visible=False,
                           yaxis_scaleanchor="x")
    st.plotly_chart(map_fig, use_container_width=True)

    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                         subplot_titles=("Speed (km/h)", "Throttle (%)", "Brake", "Gear"))
    fig.add_trace(go.Scatter(x=tel["Distance"], y=tel["Speed"], line=dict(color="#e10600")), row=1, col=1)
    fig.add_trace(go.Scatter(x=tel["Distance"], y=tel["Throttle"], line=dict(color="#00d2be")), row=2, col=1)
    fig.add_trace(go.Scatter(x=tel["Distance"], y=tel["Brake"].astype(int), line=dict(color="#f0d43a")), row=3, col=1)
    fig.add_trace(go.Scatter(x=tel["Distance"], y=tel["nGear"], line=dict(color="#a259ff")), row=4, col=1)
    fig.update_layout(template="plotly_dark", height=700, showlegend=False)
    fig.update_xaxes(title_text="Distance (m)", row=4, col=1)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Top Speed", f"{tel['Speed'].max():.0f} km/h")
    c2.metric("Avg Throttle", f"{tel['Throttle'].mean():.0f} %")
    c3.metric("Max Gear Used", int(tel["nGear"].max()))
