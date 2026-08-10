# F1 Race Engineer

A Formula 1 analytics dashboard that simulates the role of a professional
race engineer, built on real FastF1 data, Streamlit and Plotly, with a
dark, race-week style theme and a top navigation bar.

It turns raw telemetry and timing data into engineer-style insights: tyre
reads, strategy calls, driver comparisons, and a transparent statistical
model for race outcome forecasting.

## Features

| Page | What it does |
|---|---|
| Home | Race weekend overview: session leader, track temp, Safety Car count, pit stop total, top-10 result |
| Drivers | Full grid of every driver in the session as a photo card (official FastF1 headshots) |
| Teams | Constructor cards with driver lineup and session points |
| Standings | Race results, driver championship, constructor championship, full names throughout |
| Race Pace | Lap-time distribution, consistency ranking |
| Tyre Degradation | Stint breakdown, degradation slope, 0-100 tyre score |
| Pit Stops | Stop count/timing/duration, strategy score |
| Telemetry | Speed/throttle/brake/gear traces, speed-coloured circuit map |
| Comparison | Head-to-head telemetry with driver photos and a performance verdict |
| Driver Profile | Photo, bio, and full-season win/loss record: wins, podiums, poles, points, DNFs |
| Race Engineer | Synthesises the forecast, strategy, and tyre models into one radio-style briefing |
| Weather | Track/air temp, humidity, wind, rain, plus strategy notes |
| Incidents | Safety Car / VSC / flag timeline with strategy impact |
| Forecast | Transparent weighted-score win/podium probability model |
| Circuit | Track/session metadata |

All driver-facing text uses full names (e.g. "Max Verstappen") rather than
three-letter codes, no emoji are used anywhere in the UI, and navigation is
a top bar rather than a sidebar.

## Architecture

```
Top bar (season / Grand Prix / session selector + navigation)
        |
Dashboard pages (home, drivers_grid, teams_grid, standings, race_pace,
tyre_degradation, pit_stop_analysis, telemetry, driver_comparison,
driver_profile, race_engineer, weather_analysis, race_incident_analysis,
prediction, circuit_analysis)
        |
Service layer (services/fastf1_service.py: session loading, caching,
telemetry/lap/weather/results/driver-identity extraction)
        |
Data layer (FastF1 -> official F1 timing data)
```

The service layer is the only place that talks to FastF1. Every page reads
through it, and `st.cache_resource` / `st.cache_data` ensure a session is
only fetched once even if several pages ask for it.

## Project structure

```
F1-Race-Engineer/
├── dashboard/
│   ├── app.py                       # Entry point, top bar, navigation
│   ├── components/
│   │   ├── home.py
│   │   ├── drivers_grid.py
│   │   ├── teams_grid.py
│   │   ├── standings.py
│   │   ├── race_pace_analysis.py
│   │   ├── tyre_degradation.py
│   │   ├── pit_stop_analysis.py
│   │   ├── telemetry.py
│   │   ├── driver_comparison.py
│   │   ├── driver_profile.py
│   │   ├── race_engineer.py
│   │   ├── weather_analysis.py
│   │   ├── race_incident_analysis.py
│   │   ├── prediction.py
│   │   ├── strategy.py
│   │   └── circuit_analysis.py
│   ├── services/
│   │   └── fastf1_service.py
│   ├── data/                        # FastF1 cache lives here (gitignored)
│   └── config/
├── models/                          # Room to drop in a trained ML model
├── notebooks/                       # EDA / model-experiment notebooks
├── requirements.txt
├── .gitignore
└── README.md
```

## Run locally

```bash
git clone https://github.com/Sasanksurya/F1-Race-Engineer.git
cd F1-Race-Engineer
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run dashboard/app.py
```

First load of a session takes longer since FastF1 pulls from the timing
servers; every subsequent load of the same session is served from cache.

## Deploy to Streamlit Cloud

Streamlit Cloud's servers can sometimes be blocked or throttled by F1's
live-timing API — a known limitation of that hosting provider's IP
ranges, even though the exact same code works fine on your own machine.
If you deploy and see "FastF1 could not load lap data", this is why.

**The fix: pre-warm the cache locally, then commit it.**

1. On your own computer (where FastF1 already works), run:
   ```bash
   python scripts/prewarm_cache.py
   ```
   This fetches a set of real sessions (edit the `SESSIONS` list in that
   script to add/remove races) and writes them into
   `dashboard/data/ff1_cache/prewarmed/`.
2. Commit and push that cache folder along with your code:
   ```bash
   git add dashboard/data/ff1_cache/prewarmed
   git commit -m "Prewarm FastF1 cache for deployment"
   git push
   ```
3. Push this repo to GitHub, connect it on share.streamlit.io, and set
   Main file path to `dashboard/app.py`.

Once deployed, selecting one of the pre-warmed season/Grand Prix/session
combinations reads from the bundled cache instead of calling F1's
servers live, so it works reliably regardless of Streamlit Cloud's
network access. Sessions you didn't pre-warm will still attempt a live
fetch and may fail with the same network error until you add them to
`SESSIONS` and rerun the script.

## The forecast model

`components/prediction.py` uses a **real trained ML model** (scikit-learn
`RandomForestRegressor`) when one exists at
`models/finish_position_model.joblib`, predicting each driver's finishing
position from grid position, race pace, consistency, weather, and team.

If that file doesn't exist yet (e.g. a fresh clone before you've trained
one), it falls back to a transparent weighted-score formula instead, so
the app never breaks or shows nothing.

**To train the model:**
```bash
python scripts/prewarm_cache.py   # if you haven't already
python scripts/train_model.py
git add models/finish_position_model.joblib
git commit -m "Train finishing-position model"
git push
```

Honesty note: with ~8-9 races of training data, this model won't be
highly accurate — that's a limit of the data, not a bug. It's a real
model learning from data rather than a hand-tuned formula, and accuracy
improves as you add more sessions to `SESSIONS` in
`scripts/prewarm_cache.py` and `RACE_SESSIONS` in `scripts/train_model.py`,
then rerun both.

## Known engineering notes

- Large cache files: FastF1 generates big `.sqlite` / `.ff1pkl` files, kept
  out of git via `.gitignore`.
- Rate limiting: solved via `st.cache_resource` on `load_session()` so
  repeat page visits reuse one loaded session instead of re-fetching.
- Cloud path writability: the cache dir falls back to `/tmp/ff1_cache` if
  the repo-relative path isn't writable on the host.
- Driver photos come from FastF1's `HeadshotUrl` field, sourced from the
  official F1 data feed for recent seasons; older seasons may not have it
  populated, in which case the driver card simply omits the photo.
