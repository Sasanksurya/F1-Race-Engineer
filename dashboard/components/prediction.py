"""
Race Forecast
--------------------------
Uses a REAL trained ML model (scikit-learn RandomForestRegressor, see
scripts/train_model.py) when one has been trained and committed to
models/finish_position_model.joblib.

If no trained model exists yet, falls back to a transparent, rule-based
scoring formula that blends race pace, grid position, constructor
strength, and consistency — so the app never breaks or shows nothing
just because you haven't trained a model yet.

Both paths produce the same output: expected finishing position, win
probability, and podium probability per driver.
"""

import os
import streamlit as st
import numpy as np
import pandas as pd
from services import fastf1_service as ff1
from services.ml_features import extract_features, FEATURE_COLUMNS

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "finish_position_model.joblib"
)


@st.cache_resource(show_spinner=False)
def _load_trained_model():
    if not os.path.isfile(MODEL_PATH):
        return None
    try:
        import joblib
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def _predicted_positions_to_probabilities(df: pd.DataFrame, position_col: str) -> pd.DataFrame:
    """Shared conversion: a predicted/estimated finishing position per
    driver becomes a rank, then win/podium probabilities. Used for both
    the ML path and the rule-based fallback so the output looks the same
    regardless of which produced it."""
    df = df.copy()
    df["ExpectedFinish"] = df[position_col].rank(method="first").astype(int)

    # Softer positions get lower "goodness" score for the probability calc.
    max_pos = df["ExpectedFinish"].max()
    goodness = (max_pos + 1) - df["ExpectedFinish"]
    total = goodness.sum()
    df["WinProbability"] = (goodness / total * 100).round(1) if total > 0 else 0.0
    df["PodiumProbability"] = np.minimum(df["WinProbability"] * 2.4, 95).round(1)
    return df.sort_values("ExpectedFinish")


def _ml_forecast(session, drivers: list):
    model = _load_trained_model()
    if model is None:
        return None

    feats = extract_features(session, drivers)
    if feats.empty:
        return None

    X = feats[FEATURE_COLUMNS]
    feats["PredictedPosition"] = model.predict(X)
    return _predicted_positions_to_probabilities(feats, "PredictedPosition")


def _rule_based_forecast(session, drivers: list):
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
            "Driver": drv, "DriverName": name_map.get(drv, drv),
            "AvgPace": avg_pace, "Consistency": consistency,
            "Grid": grid, "TeamStrength": team_strength,
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["PaceScore"] = 1 / df["AvgPace"]
    df["ConsistencyScore"] = 1 / (df["Consistency"].fillna(df["Consistency"].mean()) + 0.01)
    df["GridScore"] = 1 / df["Grid"]
    df["TeamScore"] = df["TeamStrength"] + 1

    for col in ["PaceScore", "ConsistencyScore", "GridScore", "TeamScore"]:
        rng = df[col].max() - df[col].min()
        df[col + "_norm"] = (df[col] - df[col].min()) / rng if rng > 0 else 0.5

    df["CompositeScore"] = (
        df["PaceScore_norm"] * 0.40 + df["GridScore_norm"] * 0.25
        + df["TeamScore_norm"] * 0.25 + df["ConsistencyScore_norm"] * 0.10
    )
    # Convert to a "position" so it shares the same downstream conversion
    # as the ML path (lower score = worse position number).
    df["RuleRank"] = df["CompositeScore"].rank(ascending=False, method="first")
    return _predicted_positions_to_probabilities(df, "RuleRank")


def get_forecast(session, drivers: list):
    """
    Public entry point other components (like race_engineer.py) can call
    to get the same forecast table render() displays, without duplicating
    the ML-vs-rule-based fallback logic.
    """
    scored = _ml_forecast(session, drivers)
    if scored is None or scored.empty:
        scored = _rule_based_forecast(session, drivers)
    return scored


def render(session, drivers: list):
    st.subheader("Race Forecast")

    scored = _ml_forecast(session, drivers)
    using_ml = scored is not None and not scored.empty
    if not using_ml:
        scored = _rule_based_forecast(session, drivers)

    if scored is None or scored.empty:
        st.warning("Not enough lap data to generate a forecast for the selected drivers.")
        return

    top = scored.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Predicted Winner", top["DriverName"])
    c2.metric("Win Probability", f"{top['WinProbability']:.0f}%")
    c3.metric("Podium Probability", f"{top['PodiumProbability']:.0f}%")
    c4.metric("Expected Finish", f"P{int(top['ExpectedFinish'])}")

    st.markdown("#### Full Field Forecast")
    display_cols = ["DriverName", "ExpectedFinish", "WinProbability", "PodiumProbability"]
    st.dataframe(
        scored[display_cols].rename(columns={
            "DriverName": "Driver", "ExpectedFinish": "Expected Finish",
            "WinProbability": "Win %", "PodiumProbability": "Podium %",
        }),
        use_container_width=True, hide_index=True,
    )

    if using_ml:
        st.caption(
            "Model: trained RandomForestRegressor (scikit-learn), predicting finishing "
            "position from grid position, race pace, consistency, weather and team. "
            "See scripts/train_model.py."
        )
    else:
        st.caption(
            "Model: transparent weighted composite of race pace, grid position, "
            "constructor strength and consistency. No trained model found at "
            "models/finish_position_model.joblib — run scripts/train_model.py to enable it."
        )
