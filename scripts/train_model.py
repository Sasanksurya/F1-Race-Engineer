"""
train_model.py
---------------
Trains a REAL machine learning model (scikit-learn RandomForestRegressor)
to predict a driver's finishing position, using your prewarmed FastF1
race sessions as training data.

Run this locally, AFTER running scripts/prewarm_cache.py at least once
(this script trains on whichever race sessions are cached there):

    python scripts/train_model.py

It writes models/finish_position_model.joblib. Commit that file
alongside your code:

    git add models/finish_position_model.joblib
    git commit -m "Train finishing-position model"
    git push

Once that file exists, dashboard/components/prediction.py automatically
uses it instead of the rule-based formula. If the file is missing (e.g.
you haven't run this yet), the app falls back to the rule-based scorer
so nothing breaks.

HONESTY NOTE: with ~8-9 races of training data, this model will not be
highly accurate — that's an inherent limit of the data, not a bug. It IS
a real, trained statistical model learning patterns from data (grid
position, race pace, consistency, weather, team), not a hand-tuned
formula. Add more sessions to SESSIONS in prewarm_cache.py, re-run both
scripts, and accuracy will improve as training data grows.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "dashboard"))

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

import fastf1
from services import fastf1_service as ff1
from services.ml_features import extract_features, FEATURE_COLUMNS

CACHE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "dashboard", "data", "ff1_cache", "prewarmed"
)
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "finish_position_model.joblib")

# Same list as scripts/prewarm_cache.py — keep these in sync, or import
# one from the other if you'd rather not maintain two lists.
RACE_SESSIONS = [
    (2024, "Bahrain Grand Prix", "R"),
    (2024, "Saudi Arabian Grand Prix", "R"),
    (2024, "Australian Grand Prix", "R"),
    (2024, "Miami Grand Prix", "R"),
    (2024, "Monaco Grand Prix", "R"),
    (2024, "British Grand Prix", "R"),
    (2024, "Italian Grand Prix", "R"),
    (2024, "Abu Dhabi Grand Prix", "R"),
]


def build_training_set() -> pd.DataFrame:
    frames = []
    for year, event, session_type in RACE_SESSIONS:
        print(f"Extracting features from {year} {event} ({session_type})...")
        try:
            session = ff1.load_session(year, event, session_type)
            feats = extract_features(session)
            frames.append(feats)
            print(f"  {len(feats)} driver rows.")
        except Exception as e:
            print(f"  SKIPPED ({e})")
    if not frames:
        raise RuntimeError(
            "No training data could be built. Run scripts/prewarm_cache.py first."
        )
    data = pd.concat(frames, ignore_index=True)
    return data.dropna(subset=["FinishPosition"])


def train():
    data = build_training_set()
    print(f"\nTotal training rows: {len(data)}")

    X = data[FEATURE_COLUMNS]
    y = data["FinishPosition"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    preprocessor = ColumnTransformer(
        transformers=[("team", OneHotEncoder(handle_unknown="ignore"), ["TeamName"])],
        remainder="passthrough",
    )

    model = Pipeline(steps=[
        ("preprocess", preprocessor),
        ("regressor", RandomForestRegressor(n_estimators=200, max_depth=6, random_state=42)),
    ])

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"\nHeld-out test MAE: {mae:.2f} finishing positions")
    print("(Lower is better. With this little data, expect this to be fairly high —")
    print(" that's expected, not a bug. More prewarmed races = better accuracy.)")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\nSaved model to {MODEL_PATH}")
    print("\nNow run:")
    print("  git add models/finish_position_model.joblib")
    print('  git commit -m "Train finishing-position model"')
    print("  git push")


if __name__ == "__main__":
    train()
