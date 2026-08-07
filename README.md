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

1. Push this repo to GitHub. The `.gitignore` already keeps FastF1's cache
   files (`.sqlite` / `.ff1pkl`) out of git history.
2. On share.streamlit.io, connect the repo.
3. Set Main file path to `dashboard/app.py`.
4. Deploy. Streamlit Cloud installs `requirements.txt` automatically,
   including `streamlit-option-menu` for the top navigation bar.

## The forecast model

`components/prediction.py` uses a transparent weighted-score model, not a
trained model: it blends race pace, grid position, constructor strength
and consistency into a win/podium probability, so every number on screen
is explainable from the underlying data. If you have a trained model
(scikit-learn, XGBoost, or similar) built on historical race data, drop
its artifact into `models/` and swap the scoring function's internals in
`_score_to_probabilities()` — the rest of the app doesn't need to change.

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
