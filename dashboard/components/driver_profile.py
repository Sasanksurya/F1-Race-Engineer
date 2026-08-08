"""
Driver Profile
--------------
The complete driver record a race engineer or strategist would pull up:
photo, team, session result, and full-season wins/podiums/points/DNF
history built by walking every completed race of the season.
"""

import streamlit as st
import plotly.graph_objects as go
from services import fastf1_service as ff1


def render(session, year: int, driver_code: str):
    directory = ff1.get_driver_directory(session)
    row = directory[directory["Abbreviation"] == driver_code]
    if row.empty:
        st.warning("No driver record found for this session.")
        return
    row = row.iloc[0]
    driver_name = row.get("FullName", driver_code)
    team_color = row.get("TeamColor", "e10600")

    st.subheader("Driver Profile")

    col_photo, col_info = st.columns([1, 3])
    with col_photo:
        url = row.get("HeadshotUrlLarge") or row.get("HeadshotUrl")
        fallback_url = row.get("HeadshotUrl")
        if isinstance(url, str) and url.startswith("http"):
            st.markdown(
                f'<img src="{url}" loading="lazy" '
                f'onerror="this.onerror=null;this.src=\'{fallback_url}\';" '
                f'style="width:160px;height:160px;'
                f'object-fit:cover;object-position:top center;border-radius:12px;" />',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='width:120px;height:120px;border-radius:50%;background:#1c1f26;"
                f"display:flex;align-items:center;justify-content:center;font-size:28px;"
                f"font-weight:600;color:#{team_color};'>{driver_code}</div>",
                unsafe_allow_html=True,
            )

    with col_info:
        st.markdown(f"### {driver_name}")
        st.write(f"Team: **{row.get('TeamName', '-')}**")
        st.write(f"Country: **{row.get('CountryCode', '-')}**")
        st.write(f"Car Number: **{row.get('DriverNumber', '-')}**")
        st.write(f"This session: **P{row.get('Position', '-')}** (started P{row.get('GridPosition', '-')})")

    st.divider()
    st.markdown(f"#### {year} Season Record")

    record = ff1.get_driver_season_record(year, driver_code)

    if record.get("races", 0) == 0:
        st.info("No completed race results found yet for this driver this season.")
        return

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Races", record["races"])
    c2.metric("Wins", record["wins"])
    c3.metric("Podiums", record["podiums"])
    c4.metric("Points", record["points"])
    c5.metric("Best Finish", f"P{record['best_finish']}" if record["best_finish"] else "-")
    c6.metric("DNFs", record["dnfs"])

    if record.get("avg_finish") is not None:
        st.write(f"Average finishing position this season: **P{record['avg_finish']}**")

    log = record.get("race_log")
    if log is not None and not log.empty:
        finishes = log.dropna(subset=["Position"])
        if not finishes.empty:
            fig = go.Figure(go.Scatter(
                x=finishes["Round"], y=finishes["Position"],
                mode="lines+markers", line=dict(color=f"#{team_color}"),
            ))
            fig.update_layout(
                template="plotly_dark", height=320,
                yaxis=dict(title="Finishing Position", autorange="reversed"),
                xaxis=dict(title="Round"),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Race-by-Race Log")
        display_log = log.rename(columns={"Event": "Grand Prix"})[
            ["Round", "Grand Prix", "Position", "Points", "Status"]
        ]
        st.dataframe(display_log, use_container_width=True, hide_index=True)
