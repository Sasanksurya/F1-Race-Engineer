"""Circuit Analysis: track and session metadata."""

import streamlit as st


def render(session):
    st.subheader("Circuit Analysis")
    event = session.event
    c1, c2, c3 = st.columns(3)
    c1.metric("Circuit", event.get("Location", "-"))
    c1.metric("Country", event.get("Country", "-"))
    c2.metric("Event", event.get("EventName", "-"))
    c2.metric("Round", int(event.get("RoundNumber", 0)))
    c3.metric("Session", session.name)
    c3.metric("Date", str(event.get("EventDate", "-"))[:10])
