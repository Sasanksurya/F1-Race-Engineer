"""Teams: constructor card view with team color, car art, and driver lineup."""

import streamlit as st
from services import fastf1_service as ff1
from components.car_art import car_svg, team_car_image_path
from components.html_utils import render_html


def render(session):
    st.subheader("Teams")
    directory = ff1.get_driver_directory(session)
    teams = directory.groupby("TeamName").agg(
        TeamColor=("TeamColor", "first"),
        Drivers=("FullName", lambda x: list(x)),
        Points=("Points", "sum"),
    ).reset_index().sort_values("Points", ascending=False)

    cols_per_row = 3
    rows = [teams.iloc[i:i + cols_per_row] for i in range(0, len(teams), cols_per_row)]

    for row in rows:
        cols = st.columns(cols_per_row)
        for col, (_, team) in zip(cols, row.iterrows()):
            color = team.get("TeamColor", "e10600")
            drivers_html = "".join(f"<div>{d}</div>" for d in team["Drivers"])
            image_path = team_car_image_path(team["TeamName"])

            with col:
                with st.container(border=True):
                    render_html(f"""
                    <div style="font-size:18px;font-weight:700;color:#{color};">
                        {team['TeamName']}
                    </div>
                    """)

                    if image_path:
                        st.image(image_path, use_container_width=True)
                    else:
                        render_html(f"""
                        <div style="display:flex;justify-content:center;margin:8px 0;">
                            {car_svg(color, width=170)}
                        </div>
                        """)

                    render_html(f"""
                    <div style="font-size:12px;color:#8a92a6;margin:8px 0;">
                        {drivers_html}
                    </div>
                    <div style="font-size:13px;color:white;">
                        Session points: {team['Points']}
                    </div>
                    """)
