"""
car_art.py
----------
Visual asset for team cars.

team_car_visual() is what components should call. It looks for a real
photo you've supplied locally at dashboard/assets/cars/<team_slug>.png
(or .jpg) and uses that if present. If you haven't supplied one, it
falls back to car_svg(): an original, generic top-down race-car
silhouette tinted in the team's color.

Why no real car photos are bundled by default: actual F1 car photography
is licensed motorsport photography, and every real car photo is covered
in sponsor logos and team livery, which is trademarked/copyrighted
branding. FastF1 doesn't provide car images the way it provides driver
headshots, so there's no equivalent "official data feed" source to pull
from automatically the way get_driver_directory() does for photos.

To use real photos: source images you have the rights to use (e.g. your
own photography, or stock images licensed for this purpose), name them
to match the team, and drop them in dashboard/assets/cars/. See the
TEAM_SLUGS mapping below for exact filenames expected.
"""

import os

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "assets", "cars"
)
LOGOS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "assets", "logos"
)

TEAM_SLUGS = {
    "Red Bull Racing": "red_bull",
    "Ferrari": "ferrari",
    "Mercedes": "mercedes",
    "McLaren": "mclaren",
    "Aston Martin": "aston_martin",
    "Alpine": "alpine",
    "Williams": "williams",
    "Kick Sauber": "kick_sauber",
    "Sauber": "kick_sauber",
    "RB": "rb",
    "Haas F1 Team": "haas",
    "Haas": "haas",
}


def _find_local_file(directory: str, team_name: str):
    slug = TEAM_SLUGS.get(team_name)
    if not slug:
        return None
    for ext in ("png", "jpg", "jpeg", "webp"):
        path = os.path.join(directory, f"{slug}.{ext}")
        if os.path.isfile(path):
            return path
    return None


def car_svg(color: str = "e10600", width: int = 160) -> str:
    """An original, generic top-down race-car silhouette, not any real team's livery."""
    height = int(width * 0.42)
    return (
        f'<svg viewBox="0 0 220 100" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<ellipse cx="34" cy="50" rx="11" ry="18" fill="#15171d"/>'
        f'<ellipse cx="186" cy="50" rx="11" ry="18" fill="#15171d"/>'
        f'<rect x="10" y="42" width="38" height="16" rx="5" fill="#0a0b0f"/>'
        f'<rect x="172" y="42" width="38" height="16" rx="5" fill="#0a0b0f"/>'
        f'<path d="M60,50 Q64,32 92,30 L104,28 L116,30 L128,30 L160,32 Q184,34 190,50 '
        f'Q184,66 160,68 L128,70 L116,70 L104,70 L92,70 Q64,68 60,50 Z" fill="#{color}"/>'
        f'<path d="M34,50 L60,50" stroke="#{color}" stroke-width="7" stroke-linecap="round"/>'
        f'<path d="M158,50 L186,50" stroke="#{color}" stroke-width="7" stroke-linecap="round"/>'
        f'<ellipse cx="110" cy="50" rx="20" ry="11" fill="#0a0b0f" opacity="0.55"/>'
        f'<circle cx="110" cy="42" r="6" fill="#0a0b0f" opacity="0.7"/>'
        f'<rect x="96" y="27" width="28" height="4" rx="2" fill="#e6e8ee" opacity="0.9"/>'
        f'<rect x="30" y="47" width="10" height="6" rx="2" fill="#e6e8ee" opacity="0.85"/>'
        f'<rect x="180" y="47" width="10" height="6" rx="2" fill="#e6e8ee" opacity="0.85"/>'
        f"</svg>"
    )


def team_car_image_path(team_name: str):
    """
    Returns the local file path for a team's real car photo if you've
    supplied one, otherwise None. Callers should use st.image(path) when
    this returns something, and fall back to car_svg() when it's None.
    """
    return _find_local_file(ASSETS_DIR, team_name)


def team_logo_path(team_name: str):
    """
    Returns the local file path for a team's real logo/badge if you've
    supplied one at dashboard/assets/logos/<team_slug>.png, otherwise
    None. Separate from the car photo so you can supply either, both,
    or neither independently.
    """
    return _find_local_file(LOGOS_DIR, team_name)
