"""Teams: constructor card view with team color, car, and driver lineup."""

import streamlit as st
from services import fastf1_service as ff1


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
            with col:
                st.markdown(
                    f"""
                    <div style="border:1px solid #262b36;border-radius:10px;padding:16px;
                                background:linear-gradient(160deg, #{color}22, #11141c);
                                margin-bottom:14px;min-height:150px;">
                        <div style="font-size:18px;font-weight:700;color:#{color};">
                            {team['TeamName']}
                        </div>
                        <div style="font-size:12px;color:#8a92a6;margin:8px 0;">
                            {drivers_html}
                        </div>
                        <div style="font-size:13px;color:white;margin-top:10px;">
                            Session points: {team['Points']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
