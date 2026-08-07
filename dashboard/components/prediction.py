"""
Race Forecast
--------------------------
A transparent, rule-based scoring model (not a black box) that blends:
  - recent race pace (from lap data)
  - qualifying / grid position
  - constructor strength (session points)
  - consistency (lap time spread)
into a Win / Podium probability and expected finishing position.

This is intentionally explainable. A production version would swap
_compute_features() for a trained model (e.g. gradient boosted trees on
historical race data) while keeping the same output contract.
"""

import streamlit as st
import numpy as np
import pandas as pd
from services import fastf1_service as ff1


def _compute_features(session, drivers: list) -> pd.DataFrame:
    laps = ff1.get_all_laps(session)
    results = ff1.get_session_results(session)
    name_map = ff1.get_driver_name_map(session)
    rows = []
    for drv in drivers:
        d_laps = laps[laps["Driver"] == drv].dropna(subset=["LapTimeSeconds"])
        if d_laps.empty:
            continue
        avg_pace = d_laps["LapTimeSeconds"].mean()
        consistency = d_laps["LapTimeSeconds"].std()
        grid = results.loc[results["Abbreviation"] == drv, "GridPosition"]
        grid = float(grid.iloc[0]) if not grid.empty else 10.0
        team_points = results.loc[results["Abbreviation"] == drv, "Points"]
        team_strength = float(team_points.iloc[0]) if not team_points.empty else 0.0
        rows.append({
            "Driver": drv,
            "DriverName": name_map.get(drv, drv),
            "AvgPace": avg_pace,
            "Consistency": consistency,
            "Grid": grid,
            "TeamStrength": team_strength,
        })
    return pd.DataFrame(rows)


def _score_to_probabilities(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df["PaceScore"] = 1 / df["AvgPace"]
    df["ConsistencyScore"] = 1 / (df["Consistency"].fillna(df["Consistency"].mean()) + 0.01)
    df["GridScore"] = 1 / df["Grid"]
    df["TeamScore"] = df["TeamStrength"] + 1

    for col in ["PaceScore", "ConsistencyScore", "GridScore", "TeamScore"]:
        rng = df[col].max() - df[col].min()
        df[col + "_norm"] = (df[col] - df[col].min()) / rng if rng > 0 else 0.5

    df["CompositeScore"] = (
        df["PaceScore_norm"] * 0.40
        + df["GridScore_norm"] * 0.25
        + df["TeamScore_norm"] * 0.25
        + df["ConsistencyScore_norm"] * 0.10
    )

    total = df["CompositeScore"].sum()
    df["WinProbability"] = (df["CompositeScore"] / total * 100).round(1)
    df["PodiumProbability"] = np.minimum(df["WinProbability"] * 2.4, 95).round(1)
    df["ExpectedFinish"] = df["CompositeScore"].rank(ascending=False).astype(int)
    return df.sort_values("CompositeScore", ascending=False)


def render(session, drivers: list):
    st.subheader("Race Forecast")
    feats = _compute_features(session, drivers)
    scored = _score_to_probabilities(feats)

    if scored.empty:
        st.warning("Not enough lap data to generate a prediction for the selected drivers.")
        return

    top = scored.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Predicted Winner", top["DriverName"])
    c2.metric("Win Probability", f"{top['WinProbability']:.0f}%")
    c3.metric("Podium Probability", f"{top['PodiumProbability']:.0f}%")
    c4.metric("Expected Finish", f"P{int(top['ExpectedFinish'])}")

    st.markdown("#### Full Field Prediction")
    display_cols = ["DriverName", "ExpectedFinish", "WinProbability", "PodiumProbability"]
    st.dataframe(
        scored[display_cols].rename(columns={
            "DriverName": "Driver", "ExpectedFinish": "Expected Finish",
            "WinProbability": "Win %", "PodiumProbability": "Podium %",
        }),
        use_container_width=True, hide_index=True,
    )

    st.caption(
        "Model: transparent weighted composite of race pace, grid position, "
        "constructor strength and consistency. Not a black-box prediction."
    )
