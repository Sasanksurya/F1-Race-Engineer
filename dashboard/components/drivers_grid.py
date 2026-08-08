"""Drivers: full-grid card view of every driver in the session, with official photos."""

import streamlit as st
from services import fastf1_service as ff1
from components.html_utils import render_html


def render(session):
    st.subheader("Drivers")
    directory = ff1.get_driver_directory(session)
    directory = directory.sort_values("Position", na_position="last")

    cols_per_row = 4
    rows = [directory.iloc[i:i + cols_per_row] for i in range(0, len(directory), cols_per_row)]

    for row in rows:
        cols = st.columns(cols_per_row)
        for col, (_, drv) in zip(cols, row.iterrows()):
            team_color = drv.get("TeamColor", "e10600")
            url = drv.get("HeadshotUrlLarge") or drv.get("HeadshotUrl")
            fallback_url = drv.get("HeadshotUrl")
            has_photo = isinstance(url, str) and url.startswith("http")

            # The photo is rendered at a fixed pixel size with object-fit:
            # cover rather than stretched to the column width, and uses the
            # F1 media CDN's larger-size variant (see _upscale_headshot) so
            # faces stay sharp instead of blurring. onerror falls back to
            # the original FastF1 URL if the larger variant doesn't exist.
            if has_photo:
                photo_html = (
                    f'<img src="{url}" loading="lazy" '
                    f'onerror="this.onerror=null;this.src=\'{fallback_url}\';" '
                    f'style="width:100%;height:160px;object-fit:cover;object-position:top center;'
                    f'border-radius:8px;display:block;margin-bottom:10px;" />'
                )
            else:
                photo_html = (
                    f'<div style="width:100%;height:160px;border-radius:8px;background:#1c1f26;'
                    f'display:flex;align-items:center;justify-content:center;font-size:26px;'
                    f'font-weight:700;color:#{team_color};margin-bottom:10px;">'
                    f'{drv["Abbreviation"]}</div>'
                )

            with col:
                render_html(f"""
                <div style="border:1px solid #262b36;border-radius:10px;padding:10px;
                            background:linear-gradient(160deg, #{team_color}22, #11141c);
                            margin-bottom:14px;">
                    {photo_html}
                    <div style="font-size:11px;color:#8a92a6;letter-spacing:0.04em;">
                        {drv.get('TeamName', '-')}
                    </div>
                    <div style="font-size:16px;font-weight:700;color:white;margin-top:2px;">
                        {drv.get('FullName', drv['Abbreviation'])}
                    </div>
                    <div style="font-size:13px;color:#{team_color};margin-top:6px;">
                        Car #{drv.get('DriverNumber', '-')} &middot; {drv.get('CountryCode', '-')}
                    </div>
                </div>
                """)
