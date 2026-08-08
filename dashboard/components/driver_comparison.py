"""Driver Comparison: head-to-head telemetry, driver photos, throttle/brake efficiency, performance verdict."""

import streamlit as st
import plotly.graph_objects as go
from services import fastf1_service as ff1


def _driver_header(session, driver_code: str):
    directory = ff1.get_driver_directory(session)
    row = directory[directory["Abbreviation"] == driver_code]
    if row.empty:
        return driver_code, None, "-"
    row = row.iloc[0]
    return row.get("FullName", driver_code), row.get("HeadshotUrl"), row.get("TeamName", "-")


def render(session, driver_a: str, driver_b: str):
    name_a, photo_a, team_a = _driver_header(session, driver_a)
    name_b, photo_b, team_b = _driver_header(session, driver_b)

    st.subheader(f"Driver Comparison: {name_a} vs {name_b}")

    head_a, head_vs, head_b = st.columns([2, 1, 2])
    with head_a:
        if photo_a:
            st.markdown(
                f'<img src="{photo_a}" loading="lazy" style="width:120px;height:120px;'
                f'object-fit:cover;object-position:top center;border-radius:10px;" />',
                unsafe_allow_html=True,
            )
        st.markdown(f"**{name_a}**")
        st.caption(team_a)
    with head_vs:
        st.markdown(
            "<div style='text-align:center;padding-top:35px;font-size:22px;color:#6b7280;'>VS</div>",
            unsafe_allow_html=True,
        )
    with head_b:
        if photo_b:
            st.markdown(
                f'<img src="{photo_b}" loading="lazy" style="width:120px;height:120px;'
                f'object-fit:cover;object-position:top center;border-radius:10px;" />',
                unsafe_allow_html=True,
            )
        st.markdown(f"**{name_b}**")
        st.caption(team_b)

    st.divider()

    try:
        tel_a = ff1.get_fastest_lap_telemetry(session, driver_a)
        tel_b = ff1.get_fastest_lap_telemetry(session, driver_b)
    except Exception:
        st.warning(
            "Telemetry data isn't available for this session right now, so the speed trace "
            "can't be shown. Try reloading the session from the top bar."
        )
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tel_a["Distance"], y=tel_a["Speed"], name=name_a, line=dict(color="#e10600")))
    fig.add_trace(go.Scatter(x=tel_b["Distance"], y=tel_b["Speed"], name=name_b, line=dict(color="#00d2be")))
    fig.update_layout(
        template="plotly_dark", height=420, title="Speed Trace, Fastest Lap",
        xaxis_title="Distance (m)", yaxis_title="Speed (km/h)",
    )
    st.plotly_chart(fig, use_container_width=True)

    stats = {
        driver_a: {
            "Max Speed": tel_a["Speed"].max(),
            "Avg Speed": tel_a["Speed"].mean(),
            "Avg Throttle": tel_a["Throttle"].mean(),
            "Brake Applications": int((tel_a["Brake"].astype(int).diff() == 1).sum()),
        },
        driver_b: {
            "Max Speed": tel_b["Speed"].max(),
            "Avg Speed": tel_b["Speed"].mean(),
            "Avg Throttle": tel_b["Throttle"].mean(),
            "Brake Applications": int((tel_b["Brake"].astype(int).diff() == 1).sum()),
        },
    }

    col1, col2 = st.columns(2)
    for col, drv, name in zip([col1, col2], [driver_a, driver_b], [name_a, name_b]):
        with col:
            st.markdown(f"**{name}**")
            st.metric("Max Speed", f"{stats[drv]['Max Speed']:.0f} km/h")
            st.metric("Avg Speed", f"{stats[drv]['Avg Speed']:.1f} km/h")
            st.metric("Avg Throttle", f"{stats[drv]['Avg Throttle']:.0f} %")
            st.metric("Brake Zones", stats[drv]["Brake Applications"])

    score_a = stats[driver_a]["Max Speed"] * 0.4 + stats[driver_a]["Avg Speed"] * 0.6
    score_b = stats[driver_b]["Max Speed"] * 0.4 + stats[driver_b]["Avg Speed"] * 0.6
    winner, loser = (name_a, name_b) if score_a >= score_b else (name_b, name_a)
    margin = abs(score_a - score_b)

    st.markdown("#### Performance Verdict")
    st.success(
        f"{winner} shows the stronger overall pace advantage over {loser} "
        f"on this lap (composite speed edge of approximately {margin:.1f} km/h)."
    )
