"""Race Pace Analysis: average lap time, consistency, pace comparison."""

import streamlit as st
import plotly.express as px
from services import fastf1_service as ff1


def render(session, drivers: list):
    st.subheader("Race Pace Analysis")
    name_map = ff1.get_driver_name_map(session)

    laps = ff1.get_all_laps(session)
    laps = laps[laps["Driver"].isin(drivers)].dropna(subset=["LapTimeSeconds"]).copy()
    laps["DriverName"] = laps["Driver"].map(name_map).fillna(laps["Driver"])

    clean = laps.groupby("Driver", group_keys=False).apply(
        lambda d: d[d["LapTimeSeconds"] < d["LapTimeSeconds"].quantile(0.95)]
    )

    fig = px.box(
        clean, x="DriverName", y="LapTimeSeconds", color="DriverName",
        title="Lap Time Distribution (outliers trimmed)",
    )
    fig.update_layout(template="plotly_dark", height=420, showlegend=False, xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    summary = (
        clean.groupby("DriverName")["LapTimeSeconds"]
        .agg(AvgLap="mean", Best="min", Consistency="std")
        .sort_values("AvgLap")
        .reset_index()
        .rename(columns={"DriverName": "Driver"})
    )
    summary["Consistency"] = summary["Consistency"].round(3)
    summary["AvgLap"] = summary["AvgLap"].round(3)
    summary["Best"] = summary["Best"].round(3)
    st.dataframe(summary, use_container_width=True, hide_index=True)

    most_consistent = summary.sort_values("Consistency").iloc[0]["Driver"]
    st.info(f"Note: {most_consistent} shows the tightest lap-time spread (most consistent race pace) in this sample.")
