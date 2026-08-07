"""Tyre Degradation Analysis: compound performance loss over a stint, 0-100 tyre score."""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from services import fastf1_service as ff1

COMPOUND_COLOR = {
    "SOFT": "#e10600", "MEDIUM": "#f0d43a", "HARD": "#ffffff",
    "INTERMEDIATE": "#43b02a", "WET": "#0067ad",
}


def _tyre_score(degradation_rate: float) -> int:
    """Convert seconds-lost-per-lap into a 0-100 tyre management score (higher is better)."""
    score = 100 - min(abs(degradation_rate) * 40, 100)
    return int(max(0, round(score)))


def render(session, drivers: list):
    st.subheader("Tyre Degradation Analysis")
    name_map = ff1.get_driver_name_map(session)

    laps = ff1.get_all_laps(session)
    laps = laps[laps["Driver"].isin(drivers)].dropna(subset=["LapTimeSeconds"]).copy()
    laps["DriverName"] = laps["Driver"].map(name_map).fillna(laps["Driver"])

    stints = ff1.get_stint_data(session)
    stints = stints[stints["Driver"].isin(drivers)].copy()
    stints["DriverName"] = stints["Driver"].map(name_map).fillna(stints["Driver"])

    st.markdown("#### Stint Overview")
    fig = px.bar(
        stints, x="StintLength", y="DriverName", color="Compound", orientation="h",
        color_discrete_map=COMPOUND_COLOR, title="Stint Length by Compound",
    )
    fig.update_layout(template="plotly_dark", height=350, yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Lap-by-Lap Degradation")
    fig2 = px.line(
        laps, x="LapNumber", y="LapTimeSeconds", color="DriverName",
        title="Lap Time Trend (rising line = degrading tyre)",
    )
    fig2.update_layout(template="plotly_dark", height=380)
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Tyre Score (0-100)")
    scores = []
    for drv, grp in laps.groupby("Driver"):
        grp = grp.sort_values("LapNumber")
        if len(grp) < 3:
            continue
        slope = np.polyfit(grp["LapNumber"], grp["LapTimeSeconds"], 1)[0]
        scores.append({
            "Driver": name_map.get(drv, drv),
            "Degradation (s/lap)": round(slope, 3),
            "Tyre Score": _tyre_score(slope),
        })

    if scores:
        score_df = pd.DataFrame(scores).sort_values("Tyre Score", ascending=False)
        st.dataframe(score_df, use_container_width=True, hide_index=True)
        best = score_df.iloc[0]["Driver"]
        st.success(f"Recommendation: {best} is managing tyre wear best in this stint sample.")
