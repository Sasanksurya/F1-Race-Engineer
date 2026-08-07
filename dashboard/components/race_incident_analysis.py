"""Race Incident Analysis: safety cars, VSC, flags, and strategy impact."""

import streamlit as st
from services import fastf1_service as ff1


def render(session):
    st.subheader("Race Incident Analysis")
    rc = ff1.get_race_control_messages(session)

    incidents = rc[
        rc["Category"].isin(["SafetyCar", "VirtualSafetyCar", "Drs"])
        | rc["Flag"].isin(["YELLOW", "DOUBLE YELLOW", "RED"])
    ]

    if incidents.empty:
        st.success("No major incidents recorded for this session: clean race conditions.")
        return

    st.markdown(f"**{len(incidents)} flagged event(s) detected**")
    for _, row in incidents.iterrows():
        flag = row.get("Flag", "-")
        st.write(f"`Lap {row.get('Lap', '-')}` [{flag}] {str(row.get('Message', '')).strip()}")

    sc_count = (rc["Category"] == "SafetyCar").sum()
    vsc_count = (rc["Category"] == "VirtualSafetyCar").sum()

    st.markdown("#### Strategy Recommendation")
    if sc_count > 0:
        st.warning("Safety Car detected: flexible pit strategy recommended. Consider pitting under SC to minimize time loss.")
    if vsc_count > 0:
        st.info("Virtual Safety Car period(s) present: evaluate cheap pit-stop windows.")
    if sc_count == 0 and vsc_count == 0:
        st.success("No Safety Car or VSC periods: standard strategy execution favored.")
