"""
html_utils.py
-------------
render_html() renders a block of HTML through Streamlit safely.

Streamlit's markdown renderer follows standard Markdown rules, which
means any line starting with 4+ spaces of indentation gets treated as a
literal code block instead of being parsed as HTML. Multi-line f-string
HTML templates naturally end up indented to match the surrounding Python
code, which silently breaks rendering (you see raw "<div>...</div>" text
on the page instead of a styled box). This helper strips leading
whitespace from every line before handing it to st.markdown, so nested,
indented HTML always renders correctly regardless of how it's written
in the source file.
"""

import streamlit as st


def render_html(html: str):
    cleaned = "\n".join(line.lstrip() for line in html.strip().split("\n"))
    st.markdown(cleaned, unsafe_allow_html=True)
