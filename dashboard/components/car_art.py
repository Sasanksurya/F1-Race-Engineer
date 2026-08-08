"""
car_art.py
----------
A small reusable SVG asset: a generic, original top-down race-car
silhouette (not any specific team's real livery, logo, or sponsor
markings) tinted in a given hex color. Used to give Teams cards and the
Home hero a motorsport feel without reproducing copyrighted car designs.
"""


def car_svg(color: str = "e10600", width: int = 160) -> str:
    height = int(width * 0.42)
    return f"""
    <svg viewBox="0 0 200 90" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="30" cy="45" rx="10" ry="16" fill="#1a1d24" />
        <ellipse cx="170" cy="45" rx="10" ry="16" fill="#1a1d24" />
        <rect x="8" y="38" width="34" height="14" rx="4" fill="#0d0f14" />
        <rect x="158" y="38" width="34" height="14" rx="4" fill="#0d0f14" />
        <path d="M55,45 Q60,30 90,28 L150,28 Q168,30 172,45
                 Q168,60 150,62 L90,62 Q60,60 55,45 Z" fill="#{color}" />
        <path d="M30,45 L55,45" stroke="#{color}" stroke-width="6" stroke-linecap="round" />
        <path d="M145,45 L172,45" stroke="#{color}" stroke-width="6" stroke-linecap="round" />
        <ellipse cx="112" cy="45" rx="18" ry="10" fill="#0d0f14" opacity="0.55" />
        <rect x="94" y="26" width="36" height="5" rx="2" fill="#e6e8ee" opacity="0.85" />
    </svg>
    """
