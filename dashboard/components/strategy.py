"""
Strategy Engine
---------------
Rule-based race strategy recommendations combining tyre wear, incident
history and weather into a single actionable output. Consumed by
ai_engineer.py as one of its inputs.
"""

import numpy as np
from services import fastf1_service as ff1


def recommend_strategy(session, driver_code: str) -> dict:
    laps = ff1.get_all_laps(session)
    d_laps = laps[laps["Driver"] == driver_code].dropna(subset=["LapTimeSeconds"])
    weather = ff1.get_weather_data(session)
    rc = ff1.get_race_control_messages(session)

    recs = []

    if len(d_laps) >= 5:
        slope = np.polyfit(d_laps["LapNumber"], d_laps["LapTimeSeconds"], 1)[0]
        if slope > 0.08:
            recs.append("Tyre degradation trending up: consider an earlier pit window.")
        elif slope < 0.02:
            recs.append("Tyre wear is flat: an extended stint or undercut window is viable.")

    if weather["Rainfall"].any():
        recs.append("Rain present: keep intermediates ready and monitor track evolution lap to lap.")
    if weather["TrackTemp"].mean() > 45:
        recs.append("High track temperature: protect rear tyres in high-speed corners to avoid graining.")

    if (rc["Category"] == "SafetyCar").any():
        recs.append("Safety Car periods occurred: stay alert for a reactive, low-cost pit stop opportunity.")

    if not recs:
        recs.append("Conditions are stable: execute the planned stint strategy with no changes.")

    return {"driver": driver_code, "recommendations": recs}
