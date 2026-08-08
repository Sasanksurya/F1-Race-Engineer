"""Home: race-week hero banner + session overview KPIs."""

import streamlit as st
from services import fastf1_service as ff1
from components.car_art import car_svg


def _kpi_card(label: str, value: str, sub: str = "", accent: str = "#e10600"):
    st.markdown(
        f"""
        <div style="border:1px solid #262b36;border-radius:10px;padding:18px;
                    background:#11141c;border-top:3px solid {accent};min-height:110px;">
            <div style="font-size:12px;color:#8a92a6;letter-spacing:0.03em;">{label}</div>
            <div style="font-size:26px;font-weight:700;color:white;margin-top:6px;">{value}</div>
            <div style="font-size:12px;color:#8a92a6;margin-top:4px;">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _hero(year: int, event: str, circuit: str, country: str, round_no: int, leader_name: str, leader_team: str):
    st.markdown(
        f"""
        <div style="position:relative;overflow:hidden;border-radius:14px;
                    background:radial-gradient(circle at 15% 30%, #2a0a08, #0a0d14 70%);
                    border:1px solid #2a1216;padding:28px 30px;margin-bottom:1.5rem;">
            <div style="position:absolute;top:0;left:0;right:0;height:5px;
                        background:repeating-linear-gradient(90deg, #e10600 0 24px, #ffffff 24px 30px, #e10600 30px 54px, #11141c 54px 60px);
                        opacity:0.9;"></div>
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:20px;">
                <div>
                    <div style="font-size:12px;letter-spacing:0.12em;color:#e10600;font-weight:700;">
                        ROUND {round_no} &middot; {year} SEASON
                    </div>
                    <div style="font-size:32px;font-weight:800;color:white;margin-top:6px;line-height:1.15;">
                        {event}
                    </div>
                    <div style="font-size:13px;color:#8a92a6;margin-top:6px;">
                        {circuit}, {country}
                    </div>
                    <div style="margin-top:18px;font-size:13px;color:#8a92a6;">
                        Session leader
                    </div>
                    <div style="font-size:18px;font-weight:700;color:white;">
                        {leader_name} <span style="font-size:13px;font-weight:400;color:#8a92a6;">&middot; {leader_team}</span>
                    </div>
                </div>
                <div style="opacity:0.9;">
                    {car_svg("e10600", width=260)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(session, year: int, event: str):
    results = ff1.get_session_results(session)
    weather = ff1.get_weather_data(session)
    rc = ff1.get_race_control_messages(session)
    pit_laps = ff1.get_pit_stops(session).dropna(subset=["PitInTime"])

    leader = results.sort_values("Position").iloc[0] if not results.empty else None
    incidents = rc[rc["Category"].isin(["SafetyCar", "VirtualSafetyCar"])]
    event_info = session.event

    _hero(
        year, event,
        event_info.get("Location", "-"), event_info.get("Country", "-"),
        int(event_info.get("RoundNumber", 0)),
        leader["FullName"] if leader is not None else "-",
        leader.get("TeamName", "-") if leader is not None else "-",
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _kpi_card("Session Leader", leader["FullName"] if leader is not None else "-",
                   leader.get("TeamName", "") if leader is not None else "")
    with c2:
        _kpi_card("Track Temperature", f"{weather['TrackTemp'].mean():.1f} degC",
                   "average across session", accent="#00d2be")
    with c3:
        _kpi_card("Safety Car Periods", str(len(incidents)),
                   "SC / VSC events this session", accent="#f0d43a")
    with c4:
        _kpi_card("Total Pit Stops", str(len(pit_laps)),
                   f"across {results.shape[0]} drivers", accent="#3671C6")

    st.divider()

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown("#### Session Result (Top 10)")
        top10 = results.sort_values("Position").head(10)[
            ["Position", "FullName", "TeamName", "GridPosition", "Points"]
        ].rename(columns={"FullName": "Driver", "TeamName": "Team", "GridPosition": "Grid"})
        st.dataframe(top10, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown("#### Session Info")
        st.write(f"Season: **{year}**")
        st.write(f"Grand Prix: **{event}**")
        st.write(f"Circuit: **{event_info.get('Location', '-')}**")
        st.write(f"Country: **{event_info.get('Country', '-')}**")
        st.write(f"Round: **{int(event_info.get('RoundNumber', 0))}**")
