"""
html_utils.py
-------------
render_html() renders a block of HTML through Streamlit correctly.

st.markdown(html, unsafe_allow_html=True) still runs the string through
Streamlit's Markdown parser before treating it as HTML, and standard
Markdown rules can misinterpret indented or nested content as a literal
code block, which is why raw "<div>...</div>" text could appear on the
page instead of a styled box.

st.html() is the correct, dedicated Streamlit API for this: it renders
a string as literal HTML with no Markdown processing at all, so
indentation, nesting, and embedded dynamic content never get
misinterpreted. Requires Streamlit >= 1.36 (already the minimum pinned
in requirements.txt).
"""

import streamlit as st


def render_html(html: str):
    st.html(html)
