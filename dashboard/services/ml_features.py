"""
ml_features.py
---------------
Shared feature-extraction logic used by BOTH the training script
(scripts/train_model.py) and the live prediction component
(components/prediction.py). Keeping this in one place guarantees the
model is trained on exactly the same features it's fed at inference
time — a common source of silent ML bugs when training and serving
code drift apart.

Each row is one driver's record for one session: grid position, the
race pace and consistency they actually showed, and the weather
conditions. FinishPosition is the training target and is left as NaN
when this is called for a live forecast (grid position, pace and
weather are all knowable before/during a race; final position is what
we're trying to predict).
"""

import pandas as pd
from services import fastf1_service as ff1

FEATURE_COLUMNS = ["GridPosition", "AvgLapTime", "LapTimeStd", "TrackTemp", "Rainfall", "TeamName"]


def extract_features(session, drivers: list = None) -> pd.DataFrame:
    results = ff1.get_session_results(session)
    laps = ff1.get_all_laps(session)
    weather = ff1.get_weather_data(session)
    name_map = ff1.get_driver_name_map(session)

    track_temp = weather["TrackTemp"].mean() if not weather.empty else 25.0
    rainfall = int(bool(weather["Rainfall"].any())) if not weather.empty else 0

    target_drivers = drivers if drivers is not None else results["Abbreviation"].tolist()

    rows = []
    for code in target_drivers:
        d_laps = laps[laps["Driver"] == code].dropna(subset=["LapTimeSeconds"])
        if len(d_laps) < 3:
            continue
        result_row = results[results["Abbreviation"] == code]
        if result_row.empty:
            continue
        result_row = result_row.iloc[0]

        avg_pace = d_laps["LapTimeSeconds"].mean()
        pace_std = d_laps["LapTimeSeconds"].std()
        finish_pos = result_row.get("Position")

        rows.append({
            "Driver": code,
            "DriverName": name_map.get(code, code),
            "TeamName": result_row.get("TeamName", "Unknown"),
            "GridPosition": float(result_row.get("GridPosition") or 20),
            "AvgLapTime": float(avg_pace),
            "LapTimeStd": float(pace_std) if pd.notna(pace_std) else 0.0,
            "TrackTemp": float(track_temp),
            "Rainfall": rainfall,
            "FinishPosition": float(finish_pos) if pd.notna(finish_pos) else None,
        })

    return pd.DataFrame(rows)
