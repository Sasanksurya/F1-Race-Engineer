"""
fastf1_service.py
------------------
Central data-access layer for the F1 Race Engineer dashboard.

Every dashboard component talks to FastF1 ONLY through this module.
This keeps caching, error handling and rate-limit protection in one place,
and means components never touch the FastF1 API directly.
"""

import os
import re
import pandas as pd
import streamlit as st
import fastf1
from fastf1.core import Laps

# ----------------------------------------------------------------------
# Cache configuration
# ----------------------------------------------------------------------
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ff1_cache", "prewarmed")
try:
    os.makedirs(CACHE_DIR, exist_ok=True)
    fastf1.Cache.enable_cache(CACHE_DIR)
except Exception:
    fallback = "/tmp/ff1_cache"
    os.makedirs(fallback, exist_ok=True)
    fastf1.Cache.enable_cache(fallback)


# ----------------------------------------------------------------------
# Session loading
# ----------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading session from FastF1 / F1 timing servers...")
def load_session(year: int, event: str, session_type: str):
    """
    Load and return a fully-populated FastF1 Session object.
    Cached via st.cache_resource so every dashboard component that asks
    for the same (year, event, session_type) reuses the same object
    instead of re-fetching it from the timing servers.

    Telemetry is by far the heaviest payload FastF1 pulls in, and on a
    resource-limited host (like Streamlit Cloud's free tier) it can time
    out or fail while laps/weather/results would have succeeded fine. If
    the full load fails, we retry once without telemetry so the rest of
    the dashboard still works; telemetry-only pages will simply show a
    "not available" message for that session instead of crashing the app.
    """
    session = fastf1.get_session(year, event, session_type)
    try:
        session.load(laps=True, telemetry=True, weather=True, messages=True)
    except Exception:
        session = fastf1.get_session(year, event, session_type)
        session.load(laps=True, telemetry=False, weather=True, messages=True)

    # Confirm laps actually came through. Accessing .laps on a session that
    # didn't finish loading raises fastf1.exceptions.DataNotLoadedError;
    # we convert that into a plain RuntimeError with a clearer message so
    # it's obvious this is a load failure, not a bug in the dashboard code.
    try:
        loaded_ok = session.laps is not None and not session.laps.empty
    except Exception:
        loaded_ok = False
    if not loaded_ok:
        raise RuntimeError(
            f"FastF1 could not load lap data for {year} {event} ({session_type}). "
            f"This is usually a temporary network or timing-server issue. Try Load again."
        )

    return session



@st.cache_data(show_spinner=False)
def get_event_schedule(year: int) -> pd.DataFrame:
    """Return the season calendar (round, event name, country, date)."""
    schedule = fastf1.get_event_schedule(year)
    return schedule[schedule["RoundNumber"] > 0].reset_index(drop=True)


# ----------------------------------------------------------------------
# Laps / pace
# ----------------------------------------------------------------------
def get_all_laps(session) -> pd.DataFrame:
    laps = session.laps.copy()
    laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()
    return laps


def get_driver_laps(session, driver_code: str) -> Laps:
    return session.laps.pick_drivers(driver_code)


# ----------------------------------------------------------------------
# Telemetry
# ----------------------------------------------------------------------
def get_fastest_lap_telemetry(session, driver_code: str) -> pd.DataFrame:
    lap = session.laps.pick_drivers(driver_code).pick_fastest()
    tel = lap.get_car_data().add_distance()
    return tel


def get_position_telemetry(session, driver_code: str) -> pd.DataFrame:
    """XY track-position data for a driver's fastest lap (for the track map)."""
    lap = session.laps.pick_drivers(driver_code).pick_fastest()
    return lap.get_pos_data()


# ----------------------------------------------------------------------
# Weather
# ----------------------------------------------------------------------
def get_weather_data(session) -> pd.DataFrame:
    return session.weather_data.copy()


# ----------------------------------------------------------------------
# Race control / incidents
# ----------------------------------------------------------------------
def get_race_control_messages(session) -> pd.DataFrame:
    return session.race_control_messages.copy()


# ----------------------------------------------------------------------
# Results / driver identity
# ----------------------------------------------------------------------
def get_session_results(session) -> pd.DataFrame:
    return session.results.copy()


def _upscale_headshot(url):
    """
    FastF1's HeadshotUrl points at F1's own media CDN, which serves a
    resized crop based on a "<N>col" segment in the URL path (e.g.
    ".transform/1col/image.png" is a small thumbnail). Requesting a wider
    column count returns a genuinely higher-resolution image from the
    same CDN, rather than stretching a small one, so faces stay sharp
    and distinct instead of blurring into each other. If the URL doesn't
    match that pattern, it's returned unchanged.
    """
    if not isinstance(url, str) or not url.startswith("http"):
        return url
    return re.sub(r"/transform/\d+col/", "/transform/9col/", url)


def get_driver_directory(session) -> pd.DataFrame:
    """
    Full driver reference table for this session: code, full name, team,
    nationality, car number, headshot image URL (published by FastF1
    directly from the official F1 data feed, upscaled to a sharper size
    where possible), and current session result.
    """
    results = session.results.copy()
    if "HeadshotUrl" not in results.columns:
        results["HeadshotUrl"] = None
    results["HeadshotUrlLarge"] = results["HeadshotUrl"].apply(_upscale_headshot)
    cols = ["Abbreviation", "FullName", "TeamName", "TeamColor", "CountryCode",
            "DriverNumber", "HeadshotUrl", "HeadshotUrlLarge", "Position", "GridPosition", "Points", "Status"]
    cols = [c for c in cols if c in results.columns]
    return results[cols].drop_duplicates(subset="Abbreviation").reset_index(drop=True)


def get_driver_name_map(session) -> dict:
    """code -> full name, e.g. {'VER': 'Max Verstappen'}"""
    directory = get_driver_directory(session)
    return dict(zip(directory["Abbreviation"], directory["FullName"]))


def get_driver_headshot_map(session) -> dict:
    """code -> official headshot image URL (may be None)."""
    directory = get_driver_directory(session)
    return dict(zip(directory["Abbreviation"], directory["HeadshotUrl"]))


def full_name(session, driver_code: str) -> str:
    return get_driver_name_map(session).get(driver_code, driver_code)


# ----------------------------------------------------------------------
# Standings
# ----------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_driver_standings(year: int) -> pd.DataFrame:
    """Cumulative driver championship standings, summed across every completed race."""
    schedule = get_event_schedule(year)
    rows = []
    for _, ev in schedule.iterrows():
        try:
            race = load_session(year, ev["EventName"], "R")
            res = race.results[["Abbreviation", "FullName", "TeamName", "Points", "Position"]].copy()
            res["Round"] = ev["RoundNumber"]
            rows.append(res)
        except Exception:
            continue
    if not rows:
        return pd.DataFrame(columns=["Abbreviation", "FullName", "TeamName", "Points"])
    all_results = pd.concat(rows, ignore_index=True)
    standings = (
        all_results.groupby(["Abbreviation", "FullName", "TeamName"])["Points"]
        .sum()
        .reset_index()
        .sort_values("Points", ascending=False)
        .reset_index(drop=True)
    )
    standings.index += 1
    return standings


@st.cache_data(show_spinner="Building this driver's season record...")
def get_driver_season_record(year: int, driver_code: str) -> dict:
    """
    Full season win/loss record for one driver: races entered, wins,
    podiums, points, best/average finish, and DNF count. Built by
    walking every completed race of the season, the way a team's
    season debrief would compile it.
    """
    schedule = get_event_schedule(year)
    race_log = []
    for _, ev in schedule.iterrows():
        try:
            race = load_session(year, ev["EventName"], "R")
            row = race.results[race.results["Abbreviation"] == driver_code]
            if row.empty:
                continue
            row = row.iloc[0]
            race_log.append({
                "Event": ev["EventName"],
                "Round": int(ev["RoundNumber"]),
                "Position": row.get("Position"),
                "Points": row.get("Points", 0),
                "Status": row.get("Status", "-"),
                "Team": row.get("TeamName", "-"),
            })
        except Exception:
            continue

    if not race_log:
        return {"races": 0}

    log_df = pd.DataFrame(race_log)
    finishes_num = [f for f in log_df["Position"].tolist() if pd.notna(f)]
    wins = int((log_df["Position"] == 1).sum())
    podiums = int((log_df["Position"] <= 3).sum())
    dnfs = int((~log_df["Status"].astype(str).str.contains("Finished|\\+", na=False, regex=True)).sum())

    return {
        "races": len(log_df),
        "wins": wins,
        "podiums": podiums,
        "points": round(log_df["Points"].sum(), 1),
        "best_finish": int(min(finishes_num)) if finishes_num else None,
        "avg_finish": round(sum(finishes_num) / len(finishes_num), 1) if finishes_num else None,
        "dnfs": dnfs,
        "team": log_df.iloc[-1]["Team"] if not log_df.empty else "-",
        "race_log": log_df,
    }


# ----------------------------------------------------------------------
# Tyres / pit stops
# ----------------------------------------------------------------------
def get_stint_data(session) -> pd.DataFrame:
    laps = session.laps.copy()
    stints = (
        laps[["Driver", "Stint", "Compound", "LapNumber"]]
        .groupby(["Driver", "Stint", "Compound"])
        .agg(StartLap=("LapNumber", "min"), EndLap=("LapNumber", "max"))
        .reset_index()
    )
    stints["StintLength"] = stints["EndLap"] - stints["StartLap"] + 1
    return stints


def get_pit_stops(session) -> pd.DataFrame:
    laps = session.laps.copy()
    pit_laps = laps[laps["PitOutTime"].notna() | laps["PitInTime"].notna()]
    return pit_laps[["Driver", "LapNumber", "PitInTime", "PitOutTime"]]
