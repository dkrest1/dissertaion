#!/usr/bin/env python3
"""Train an Isolation Forest on data_for_model.csv and save anomaly scores.

Outputs:
- anomaly_scores.csv  (run_dir, repo, run_id, score, is_anomaly)
- models/isolation_forest.joblib

This script expects `data_for_model.csv` to exist in the repo root.
"""
import os
from pathlib import Path
import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import joblib


def main():
    root = Path(__file__).resolve().parent
    data_path = root / "data_for_model.csv"
    if not data_path.exists():
        raise SystemExit(f"Missing {data_path}. Run prepare_features.py first.")

    df = pd.read_csv(data_path)

    # preserve identifiers
    id_cols = [c for c in ["run_dir", "repo", "run_id"] if c in df.columns]

    # pick numeric columns only
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        raise SystemExit("No numeric columns found in data_for_model.csv to train on.")

    X = df[numeric_cols].fillna(0)

    # scale features
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    # fit Isolation Forest
    clf = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    clf.fit(Xs)

    # decision_function: higher means more normal; lower (more negative) -> anomaly
    scores = clf.decision_function(Xs)
    preds = clf.predict(Xs)  # 1 == normal, -1 == anomaly

    out = df[id_cols].copy() if id_cols else pd.DataFrame()
    out = out.reset_index(drop=True)
    out["score"] = scores
    out["anomaly"] = (preds == -1)

    out_path = root / "anomaly_scores.csv"
    out.to_csv(out_path, index=False)

    # save model and scaler
    model_dir = root / "models"
    model_dir.mkdir(exist_ok=True)
    joblib.dump({"scaler": scaler, "model": clf}, model_dir / "isolation_forest.joblib")

    # print a short summary
    total = len(out)
    n_anom = int(out["anomaly"].sum())
    print(f"Trained Isolation Forest on {total} rows. Detected {n_anom} anomalies ({n_anom/total:.2%}).")

    # show top anomalies (lowest scores)
    sample = out.sort_values("score").head(10)
    print("Top anomalies (lowest scores):")
    print(sample[[c for c in id_cols if c in sample.columns] + ["score", "anomaly"]].to_string(index=False))


if __name__ == "__main__":
    main()
