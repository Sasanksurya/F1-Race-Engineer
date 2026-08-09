"""Teams: constructor card view with team color, logo, car art, and driver lineup."""

import streamlit as st
from services import fastf1_service as ff1
from components.car_art import car_svg, team_car_image_path, team_logo_path
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
            car_image_path = team_car_image_path(team["TeamName"])
            logo_path = team_logo_path(team["TeamName"])

            with col:
                with st.container(border=True):
                    name_col, logo_col = st.columns([4, 1])
                    with name_col:
                        render_html(
                            f'<div style="font-size:18px;font-weight:700;color:#{color};">'
                            f'{team["TeamName"]}</div>'
                        )
                    with logo_col:
                        if logo_path:
                            st.image(logo_path, use_container_width=True)

                    if car_image_path:
                        st.image(car_image_path, use_container_width=True)
                    else:
                        render_html(
                            '<div style="display:flex;justify-content:center;margin:8px 0;">'
                            f'{car_svg(color, width=170)}</div>'
                        )

                    render_html(
                        f'<div style="font-size:12px;color:#8a92a6;margin:8px 0;">'
                        f'{drivers_html}</div>'
                        f'<div style="font-size:13px;color:white;">'
                        f'Session points: {team["Points"]}</div>'
                    )
