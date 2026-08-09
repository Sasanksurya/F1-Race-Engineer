"""Pit Stop Strategy Analysis: count, timing, average duration, strategy score."""

import streamlit as st
import pandas as pd
import plotly.express as px
from services import fastf1_service as ff1


def render(session, drivers: list):
    st.subheader("Pit Stop Strategy Analysis")
    name_map = ff1.get_driver_name_map(session)

    laps = ff1.get_all_laps(session)
    laps = laps[laps["Driver"].isin(drivers)].copy()
    laps["DriverName"] = laps["Driver"].map(name_map).fillna(laps["Driver"])

    pit_laps = laps.dropna(subset=["PitInTime"]).copy()
    if pit_laps.empty:
        st.info("No pit stops recorded for the selected drivers in this session.")
        return

    pit_laps["PitDuration"] = (pit_laps["PitOutTime"] - pit_laps["PitInTime"]).dt.total_seconds()

    # Some pit-in laps (e.g. the very last lap, or a lap under red flag) never
    # get a matching pit-out time, which leaves PitDuration as NaN. Plotly's
    # marker "size" can't be NaN, so drop those rows from the chart only.
    plot_laps = pit_laps.dropna(subset=["PitDuration"]).copy()
    plot_laps = plot_laps[plot_laps["PitDuration"] > 0]

    if plot_laps.empty:
        st.info("Pit stops were recorded, but stop duration couldn't be calculated for this session (missing pit-out timing).")
    else:
        fig = px.scatter(
            plot_laps, x="LapNumber", y="DriverName", size="PitDuration", color="DriverName",
            title="Pit Stop Timing (bubble size = stop duration)",
        )
        fig.update_layout(template="plotly_dark", height=380, showlegend=False, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    summary = pit_laps.groupby("DriverName").agg(
        Stops=("LapNumber", "count"), AvgPitTime=("PitDuration", "mean")
    ).reset_index().rename(columns={"DriverName": "Driver"})
    summary["AvgPitTime"] = summary["AvgPitTime"].round(2)
    # AvgPitTime can still be NaN for a driver whose only stop had no pit-out
    # time; treat that as a neutral (zero time-loss) contribution to the score.
    summary["StrategyScore"] = (100 - (summary["Stops"] * 8 + summary["AvgPitTime"].fillna(0))).clip(lower=0).round(1)
    summary = summary.sort_values("StrategyScore", ascending=False)
    display_summary = summary.copy()
    display_summary["AvgPitTime"] = display_summary["AvgPitTime"].apply(
        lambda v: f"{v:.2f}s" if pd.notna(v) else "N/A"
    )
    st.dataframe(display_summary, use_container_width=True, hide_index=True)

    if not summary.empty:
        best = summary.iloc[0]["Driver"]
        st.success(f"Note: {best} ran the most time-efficient pit strategy (fewest stops, fastest average stationary time).")
