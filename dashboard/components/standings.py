"""Race Results, Driver Championship, and Constructor Championship standings."""

import streamlit as st
import plotly.express as px
from services import fastf1_service as ff1


def render_race_results(session):
    st.subheader("Race / Session Results")
    results = ff1.get_session_results(session)
    table = results[["Position", "FullName", "TeamName", "GridPosition", "Points", "Status"]]
    table = table.rename(columns={
        "FullName": "Driver", "TeamName": "Team",
        "GridPosition": "Grid", "Status": "Result",
    })
    st.dataframe(table, use_container_width=True, hide_index=True)


def render_championship(year: int):
    st.subheader("Driver Championship Standings")
    standings = ff1.get_driver_standings(year)
    if standings.empty:
        st.warning("No completed races found yet for this season.")
        return
    fig = px.bar(
        standings.head(10), x="Points", y="FullName", orientation="h",
        color="TeamName", title=f"{year} Driver Championship (Top 10)",
    )
    fig.update_layout(template="plotly_dark", yaxis=dict(autorange="reversed", title=""), height=450)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        standings.rename(columns={"FullName": "Driver", "TeamName": "Team"}),
        use_container_width=True,
    )


def render_constructors(year: int):
    st.subheader("Constructor Championship")
    standings = ff1.get_driver_standings(year)
    if standings.empty:
        st.warning("No completed races found yet for this season.")
        return
    constructors = standings.groupby("TeamName")["Points"].sum().reset_index()
    constructors = constructors.sort_values("Points", ascending=False)
    fig = px.bar(
        constructors, x="TeamName", y="Points", color="TeamName",
        title=f"{year} Constructor Championship",
    )
    fig.update_layout(template="plotly_dark", height=450, showlegend=False, xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)
