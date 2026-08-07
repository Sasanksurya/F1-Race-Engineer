"""
Race Engineer
---------------------------
The final intelligence layer: combines the prediction engine, strategy
engine, tyre analysis and race conditions into a single, professional
"race engineer on the radio" style briefing for a chosen driver.
"""

import streamlit as st
import numpy as np
from services import fastf1_service as ff1
from components.strategy import recommend_strategy
from components.prediction import _compute_features, _score_to_probabilities


def _tyre_note(session, driver_code: str) -> str:
    laps = ff1.get_all_laps(session)
    d_laps = laps[laps["Driver"] == driver_code].dropna(subset=["LapTimeSeconds"])
    if len(d_laps) < 5:
        return "insufficient lap data for a tyre read"

    slope = np.polyfit(d_laps["LapNumber"], d_laps["LapTimeSeconds"], 1)[0]
    if slope > 0.08:
        return "tyres degrading quickly, prioritise preservation"
    if slope < 0.02:
        return "tyres holding up well, pace can be pushed"
    return "tyre wear is moderate and under control"


def render(session, driver_code: str, field: list):
    driver_name = ff1.full_name(session, driver_code)

    st.subheader("Race Engineer")
    st.caption(
        f"Live-style briefing for {driver_name}, synthesised from the prediction, "
        f"strategy, tyre and weather models."
    )

    feats = _compute_features(session, field)
    scored = _score_to_probabilities(feats)
    result_row = scored[scored["Driver"] == driver_code]
    strategy = recommend_strategy(session, driver_code)
    tyre_note = _tyre_note(session, driver_code)

    if not result_row.empty:
        r = result_row.iloc[0]
        st.markdown(
            f"> \"Copy. Current pace puts you around P{int(r['ExpectedFinish'])}, "
            f"win probability {r['WinProbability']:.0f} percent, podium chance "
            f"{r['PodiumProbability']:.0f} percent. {tyre_note.capitalize()}.\""
        )
    else:
        st.markdown(f"> \"Copy. {tyre_note.capitalize()}.\"")

    st.markdown("#### Strategy Directives")
    for rec in strategy["recommendations"]:
        st.write(f"- {rec}")

    st.markdown("#### Engineer's Summary")
    st.success(
        "Focus on consistency, tyre preservation and minimising performance loss "
        "through the remaining stint. React to Safety Car and weather windows as they open."
    )
