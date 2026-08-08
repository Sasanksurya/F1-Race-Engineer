"""
prewarm_cache.py
-----------------
Run this ONCE, LOCALLY, on a normal home/office network (not on
Streamlit Cloud). It fetches a set of real FastF1 sessions and writes
them into dashboard/data/ff1_cache/prewarmed/.

Why this exists: Streamlit Cloud's servers can be blocked or throttled
by F1's live-timing API, a known limitation of that hosting provider,
even though the exact same code works fine on your own machine. The
fix is to fetch the data once locally, commit the resulting cache
folder to git, and have the deployed app read from that bundled cache
instead of calling F1's servers at all.

Usage:
    python scripts/prewarm_cache.py

After it finishes, commit and push the new files under
dashboard/data/ff1_cache/prewarmed/ along with your code:

    git add dashboard/data/ff1_cache/prewarmed
    git commit -m "Prewarm FastF1 cache for deployment"
    git push

Edit SESSIONS below to add or remove races/sessions as needed. Keep
the list reasonably small: each session's cache is a few MB, and every
extra session is more data committed to your GitHub repo.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "dashboard"))

import fastf1  # noqa: E402

CACHE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "dashboard", "data", "ff1_cache", "prewarmed"
)
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

# (year, event name as it appears in the season schedule, session type)
# session type: "R" Race, "Q" Qualifying, "FP1"/"FP2"/"FP3" Practice, "S" Sprint
SESSIONS = [
    (2024, "Bahrain Grand Prix", "R"),
    (2024, "Bahrain Grand Prix", "Q"),
    (2024, "Saudi Arabian Grand Prix", "R"),
    (2024, "Australian Grand Prix", "R"),
    (2024, "Miami Grand Prix", "R"),
    (2024, "Monaco Grand Prix", "R"),
    (2024, "British Grand Prix", "R"),
    (2024, "Italian Grand Prix", "R"),
    (2024, "Abu Dhabi Grand Prix", "R"),
]

if __name__ == "__main__":
    for year, event, session_type in SESSIONS:
        print(f"Fetching {year} {event} ({session_type})...")
        try:
            session = fastf1.get_session(year, event, session_type)
            session.load(laps=True, telemetry=True, weather=True, messages=True)
            print(f"  OK: {len(session.laps)} laps loaded.")
        except Exception as e:
            print(f"  FAILED: {e}")

    print("\nDone. Now run:")
    print("  git add dashboard/data/ff1_cache/prewarmed")
    print("  git commit -m \"Prewarm FastF1 cache for deployment\"")
    print("  git push")
