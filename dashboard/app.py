"""
F1 Race Engineer: main Streamlit entry point.

Run locally with:
    streamlit run dashboard/app.py

Deploys directly on Streamlit Cloud pointing at this file.
"""

import os
import sys
import streamlit as st
from streamlit_option_menu import option_menu

sys.path.append(os.path.dirname(__file__))

from services import fastf1_service as ff1
from components import (
    home, weather_analysis, race_incident_analysis, standings, race_pace_analysis,
    tyre_degradation, pit_stop_analysis, telemetry, driver_comparison,
    prediction, race_engineer, driver_profile, circuit_analysis,
    drivers_grid, teams_grid,
)

st.set_page_config(
    page_title="F1 Race Engineer", page_icon=":checkered_flag:",
    layout="wide", initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------
# F1-style dark theme
# ---------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@400;600;700;900&display=swap');

    html, body, [class*="css"]  { font-family: 'Titillium Web', sans-serif !important; }

    /* Force the dark background on every container Streamlit renders,
       across versions: some ship stApp, others stAppViewContainer/stMain. */
    html, body,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stHeader"],
    .main {
        background-color: #0a0d14 !important;
    }
    [data-testid="stHeader"] { background-color: transparent !important; }
    section[data-testid="stSidebar"] { display: none !important; }

    /* Default body/paragraph text: Streamlit's light-theme default is
       near-black, which disappears on a dark background unless overridden. */
    p, span, label, div, li, .stMarkdown, .stCaption {
        color: #e6e8ee;
    }
    h1, h2, h3, h4 { font-family: 'Titillium Web', sans-serif; font-weight: 700; color: #ffffff !important; }

    div[data-testid="stMetric"] {
        background-color: #11141c;
        border: 1px solid #262b36;
        border-top: 3px solid #e10600;
        border-radius: 10px;
        padding: 12px 16px 8px 16px;
    }
    div[data-testid="stMetricLabel"] { color: #8a92a6 !important; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #11141c; border-radius: 8px 8px 0 0;
        color: #8a92a6; padding: 8px 18px;
    }
    .stTabs [aria-selected="true"] { color: #ffffff !important; border-bottom: 3px solid #e10600; }

    /* Select boxes and multiselect in the top bar */
    div[data-baseweb="select"] > div { background-color: #11141c !important; border-color: #262b36 !important; color: #ffffff !important; }
    div[data-baseweb="select"] span { color: #ffffff !important; }

    .block-container { padding-top: 1.2rem; }

    .f1-topbar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 6px 0 14px 0; margin-bottom: 4px;
    }
    .f1-logo { display: flex; align-items: center; gap: 10px; }
    .f1-logo-mark {
        width: 34px; height: 34px; border-radius: 8px;
        background: linear-gradient(135deg, #e10600, #8b0000);
        display: flex; align-items: center; justify-content: center;
        font-weight: 900; color: #ffffff !important; font-size: 16px;
    }
    .f1-logo-text { font-size: 19px; font-weight: 800; color: #ffffff !important; letter-spacing: 0.01em; }
    .f1-logo-sub { font-size: 11px; color: #8a92a6 !important; margin-top: -2px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Top bar: logo + season / event / session selector
# ---------------------------------------------------------------------
logo_col, season_col, event_col, session_col, load_col = st.columns([3, 1.1, 2, 1.3, 1])

with logo_col:
    st.markdown(
        """
        <div class="f1-topbar">
            <div class="f1-logo">
                <div class="f1-logo-mark">RE</div>
                <div>
                    <div class="f1-logo-text">Race Engineer Dashboard</div>
                    <div class="f1-logo-sub">Live timing, telemetry &amp; strategy, powered by FastF1</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with season_col:
    year = st.selectbox("Season", options=list(range(2024, 2018, -1)), index=0, label_visibility="collapsed")

try:
    schedule = ff1.get_event_schedule(year)
except Exception as e:
    st.error(f"Could not load calendar: {e}")
    st.stop()

with event_col:
    event = st.selectbox("Grand Prix", options=schedule["EventName"].tolist(), label_visibility="collapsed")

with session_col:
    session_type = st.selectbox(
        "Session", options=["R", "Q", "FP1", "FP2", "FP3", "S", "SQ"],
        format_func=lambda x: {
            "R": "Race", "Q": "Qualifying", "FP1": "Practice 1", "FP2": "Practice 2",
            "FP3": "Practice 3", "S": "Sprint", "SQ": "Sprint Qualifying",
        }[x],
        label_visibility="collapsed",
    )

with load_col:
    load_clicked = st.button("Load", type="primary", use_container_width=True)

if "session_obj" not in st.session_state:
    st.session_state.session_obj = None

if load_clicked or st.session_state.session_obj is None:
    try:
        st.session_state.session_obj = ff1.load_session(year, event, session_type)
    except Exception as e:
        st.error(f"Failed to load session data from FastF1: {e}")
        st.stop()

session = st.session_state.session_obj
drivers = sorted(session.laps["Driver"].dropna().unique().tolist())
if not drivers:
    st.warning("No lap data available for this session yet.")
    st.stop()

name_map = ff1.get_driver_name_map(session)


def _label(code: str) -> str:
    return name_map.get(code, code)


# ---------------------------------------------------------------------
# Top navigation bar (replaces the sidebar)
# ---------------------------------------------------------------------
selected = option_menu(
    menu_title=None,
    options=[
        "Home", "Drivers", "Teams", "Standings", "Race Pace", "Tyre Degradation",
        "Pit Stops", "Telemetry", "Comparison", "Driver Profile", "Race Engineer",
        "Weather", "Incidents", "Forecast", "Circuit",
    ],
    icons=[
        "house", "person-badge", "people", "trophy", "speedometer2", "circle-half",
        "stopwatch", "broadcast", "arrow-left-right", "person-lines-fill", "mic",
        "cloud-sun", "exclamation-triangle", "graph-up-arrow", "geo-alt",
    ],
    orientation="horizontal",
    styles={
        "container": {"background-color": "#11141c", "padding": "6px 8px", "border-radius": "10px"},
        "icon": {"color": "#8a92a6", "font-size": "14px"},
        "nav-link": {"font-size": "13px", "color": "#c7cad1", "padding": "8px 12px",
                     "--hover-color": "#1b1f2a"},
        "nav-link-selected": {"background-color": "#e10600", "color": "white", "font-weight": "600"},
    },
)

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Driver pickers, shown only on pages that need them
# ---------------------------------------------------------------------
needs_focus = selected in ("Comparison", "Driver Profile", "Telemetry", "Race Engineer")
needs_pool = selected in ("Race Pace", "Tyre Degradation", "Pit Stops", "Forecast", "Race Engineer")

main_driver = compare_driver = None
compare_pool = drivers[:5]

if needs_focus or selected == "Comparison":
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        main_driver = st.selectbox("Primary driver", options=drivers, format_func=_label)
    if selected == "Comparison":
        with fc2:
            compare_driver = st.selectbox(
                "Compare against", options=[d for d in drivers if d != main_driver],
                format_func=_label,
            )
elif needs_pool:
    compare_pool = st.multiselect(
        "Drivers to include", options=drivers, default=drivers[:6], format_func=_label,
    ) or drivers[:6]

if main_driver is None:
    main_driver = drivers[0]
if compare_driver is None:
    compare_driver = drivers[1] if len(drivers) > 1 else drivers[0]

st.divider()

# ---------------------------------------------------------------------
# Page dispatch
# ---------------------------------------------------------------------
if selected == "Home":
    home.render(session, year, event)
elif selected == "Drivers":
    drivers_grid.render(session)
elif selected == "Teams":
    teams_grid.render(session)
elif selected == "Standings":
    tab1, tab2, tab3 = st.tabs(["Race Results", "Driver Championship", "Constructors"])
    with tab1:
        standings.render_race_results(session)
    with tab2:
        standings.render_championship(year)
    with tab3:
        standings.render_constructors(year)
elif selected == "Race Pace":
    race_pace_analysis.render(session, compare_pool)
elif selected == "Tyre Degradation":
    tyre_degradation.render(session, compare_pool)
elif selected == "Pit Stops":
    pit_stop_analysis.render(session, compare_pool)
elif selected == "Telemetry":
    telemetry.render(session, main_driver)
elif selected == "Comparison":
    driver_comparison.render(session, main_driver, compare_driver)
elif selected == "Driver Profile":
    driver_profile.render(session, year, main_driver)
elif selected == "Race Engineer":
    race_engineer.render(session, main_driver, compare_pool)
elif selected == "Weather":
    weather_analysis.render(session)
elif selected == "Incidents":
    race_incident_analysis.render(session)
elif selected == "Forecast":
    prediction.render(session, compare_pool)
elif selected == "Circuit":
    circuit_analysis.render(session)

st.markdown(
    "<div style='text-align:center;color:#4b5164;font-size:12px;padding:24px 0 8px;'>"
    "Built with FastF1, Streamlit and Plotly</div>",
    unsafe_allow_html=True,
)
