"""Weather Analysis: track/air temperature, humidity, wind, rain, and strategy notes."""

import streamlit as st
import plotly.graph_objects as go
from services import fastf1_service as ff1


def _ai_weather_recommendation(weather) -> list:
    notes = []
    track_temp = weather["TrackTemp"].mean()
    humidity = weather["Humidity"].mean()
    rain = weather["Rainfall"].any()

    if rain:
        notes.append("Rain detected: wet-weather setup and intermediate or wet tyres should be on standby.")
    if track_temp > 45:
        notes.append("High track temperature: elevated tyre overheating and graining risk on soft compounds.")
    elif track_temp < 25:
        notes.append("Cold track: expect a longer tyre warm-up window, watch out-lap pace.")
    if humidity > 70:
        notes.append("High humidity: reduced cooling efficiency, monitor power-unit temperatures.")
    if not notes:
        notes.append("Stable conditions: no major weather-driven strategy risk identified.")
    return notes


def render(session):
    st.subheader("Weather Analysis")
    weather = ff1.get_weather_data(session)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Track Temp", f"{weather['TrackTemp'].mean():.1f} degC")
    c2.metric("Air Temp", f"{weather['AirTemp'].mean():.1f} degC")
    c3.metric("Humidity", f"{weather['Humidity'].mean():.1f} %")
    c4.metric("Wind Speed", f"{weather['WindSpeed'].mean():.1f} m/s")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weather["Time"].dt.total_seconds() / 60, y=weather["TrackTemp"],
        name="Track Temp", line=dict(color="#e10600"),
    ))
    fig.add_trace(go.Scatter(
        x=weather["Time"].dt.total_seconds() / 60, y=weather["AirTemp"],
        name="Air Temp", line=dict(color="#00d2be"),
    ))
    fig.update_layout(
        template="plotly_dark", height=380,
        xaxis_title="Session Time (min)", yaxis_title="Temperature (degC)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Race Engineer Notes")
    for note in _ai_weather_recommendation(weather):
        st.info(note)
