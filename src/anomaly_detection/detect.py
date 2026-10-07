"""
Ride anomaly detection for RideFlow.

IMPORTANT: Flags indicate potential anomalies / rides requiring review.
This is an analytical screening mechanism, NOT fraud confirmation.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings
from src.utils.db import get_engine
from src.utils.logging_config import setup_logging


def _load_completed_rides(engine) -> pd.DataFrame:
    """Prefer warehouse fact; fall back to raw."""
    queries = [
        """
        SELECT
            ride_id, user_id, driver_id, request_timestamp AS ts,
            total_fare AS fare, distance_km, duration_minutes,
            surge_multiplier, city_id, ride_status
        FROM warehouse.fact_rides
        WHERE is_completed = TRUE
        """,
        """
        SELECT
            ride_id, user_id, driver_id,
            request_timestamp::timestamp AS ts,
            total_fare AS fare, distance_km, duration_minutes,
            surge_multiplier, city_id, ride_status
        FROM raw.rides
        WHERE LOWER(ride_status) = 'completed'
          AND total_fare IS NOT NULL
        """,
    ]
    with engine.connect() as conn:
        for q in queries:
            try:
                return pd.read_sql(q, conn)
            except Exception:
                continue
    return pd.DataFrame()


def rule_based_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Apply documented business rules for unusual rides."""
    rows: List[Dict[str, Any]] = []
    if df.empty:
        return pd.DataFrame(rows)

    fare_p99 = df["fare"].quantile(0.99)
    dist_p99 = df["distance_km"].quantile(0.99)
    dist_p01 = df["distance_km"].quantile(0.01)
    dur_p99 = df["duration_minutes"].quantile(0.99)

    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
    df["hour"] = df["ts"].dt.hour

    # Multiple rides in short window per user
    df = df.sort_values(["user_id", "ts"])
    df["prev_ts"] = df.groupby("user_id")["ts"].shift(1)
    df["minutes_since_prev"] = (df["ts"] - df["prev_ts"]).dt.total_seconds() / 60.0

    for _, r in df.iterrows():
        reasons: List[str] = []
        score = 0.0
        if pd.notna(r["fare"]) and r["fare"] > fare_p99 * 1.2:
            reasons.append("Extremely high fare vs city distribution")
            score += 2.0
        if pd.notna(r["distance_km"]) and r["distance_km"] > dist_p99:
            reasons.append("Extremely long ride")
            score += 1.5
        if pd.notna(r["distance_km"]) and r["distance_km"] < max(0.3, dist_p01):
            reasons.append("Extremely short ride")
            score += 1.0
        if pd.notna(r["duration_minutes"]) and r["duration_minutes"] > dur_p99:
            reasons.append("Extremely long duration")
            score += 1.0
        if pd.notna(r.get("minutes_since_prev")) and r["minutes_since_prev"] < 5:
            reasons.append("Multiple rides within a short time")
            score += 2.0
        if pd.notna(r.get("hour")) and r["hour"] in (1, 2, 3) and pd.notna(r["fare"]) and r["fare"] > fare_p99:
            reasons.append("Unusual late-night high-value activity")
            score += 1.5
        if reasons:
            severity = (
                "Critical" if score >= 5 else "High" if score >= 3.5 else "Medium" if score >= 2 else "Low"
            )
            rows.append(
                {
                    "ride_id": int(r["ride_id"]),
                    "user_id": int(r["user_id"]) if pd.notna(r["user_id"]) else None,
                    "driver_id": int(r["driver_id"]) if pd.notna(r["driver_id"]) else None,
                    "timestamp": r["ts"],
                    "fare": float(r["fare"]) if pd.notna(r["fare"]) else None,
                    "rule_based_score": score,
                    "ml_anomaly_score": None,
                    "anomaly_reason": "; ".join(reasons),
                    "severity": severity,
                }
            )
    return pd.DataFrame(rows)


def zscore_flags(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Customer-level fare z-score anomalies."""
    rows: List[Dict[str, Any]] = []
    if df.empty or "user_id" not in df.columns:
        return pd.DataFrame(rows)

    stats = df.groupby("user_id")["fare"].agg(["mean", "std", "count"]).reset_index()
    stats = stats[stats["count"] >= 5]
    merged = df.merge(stats, on="user_id", how="inner")
    merged["z_score"] = (merged["fare"] - merged["mean"]) / merged["std"].replace(0, np.nan)
    flagged = merged[merged["z_score"].abs() >= threshold]

    for _, r in flagged.iterrows():
        rows.append(
            {
                "ride_id": int(r["ride_id"]),
                "user_id": int(r["user_id"]),
                "driver_id": int(r["driver_id"]) if pd.notna(r["driver_id"]) else None,
                "timestamp": pd.to_datetime(r["ts"], errors="coerce"),
                "fare": float(r["fare"]),
                "rule_based_score": abs(float(r["z_score"])),
                "ml_anomaly_score": None,
                "anomaly_reason": f"Fare z-score {r['z_score']:.2f} (threshold={threshold})",
                "severity": "High" if abs(r["z_score"]) >= threshold + 1 else "Medium",
            }
        )
    return pd.DataFrame(rows)


def isolation_forest_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Optional Isolation Forest screening scores."""
    if df.empty or len(df) < 100:
        return pd.DataFrame()

    work = df.copy()
    work["ts"] = pd.to_datetime(work["ts"], errors="coerce")
    work["hour_of_day"] = work["ts"].dt.hour.fillna(12)
    work = work.sort_values(["user_id", "ts"])
    work["rides_last_1_hour"] = (
        work.groupby("user_id")["ts"]
        .transform(lambda s: s.diff().dt.total_seconds().lt(3600).astype(int))
        .fillna(0)
    )
    user_avg = work.groupby("user_id")["fare"].transform("mean")
    work["fare_vs_user_average"] = work["fare"] / user_avg.replace(0, np.nan)

    features = [
        "fare",
        "distance_km",
        "duration_minutes",
        "surge_multiplier",
        "hour_of_day",
        "rides_last_1_hour",
        "fare_vs_user_average",
    ]
    X = work[features].fillna(0).astype(float)
    model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
    work["ml_pred"] = model.fit_predict(X)
    work["ml_anomaly_score"] = -model.score_samples(X)  # higher = more anomalous
    flagged = work[work["ml_pred"] == -1]

    rows = []
    for _, r in flagged.iterrows():
        rows.append(
            {
                "ride_id": int(r["ride_id"]),
                "user_id": int(r["user_id"]) if pd.notna(r["user_id"]) else None,
                "driver_id": int(r["driver_id"]) if pd.notna(r["driver_id"]) else None,
                "timestamp": r["ts"],
                "fare": float(r["fare"]) if pd.notna(r["fare"]) else None,
                "rule_based_score": None,
                "ml_anomaly_score": float(r["ml_anomaly_score"]),
                "anomaly_reason": "Isolation Forest unusual pattern (screening only)",
                "severity": "Medium",
            }
        )
    return pd.DataFrame(rows)


def persist_anomalies(engine, anomalies: pd.DataFrame) -> int:
    if anomalies.empty:
        return 0
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE monitoring.ride_anomalies RESTART IDENTITY"))
        anomalies = anomalies.copy()
        anomalies["detected_at"] = datetime.utcnow()
        anomalies.to_sql(
            "ride_anomalies",
            conn,
            schema="monitoring",
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )
    return len(anomalies)


def run_anomaly_detection() -> Dict[str, Any]:
    settings = get_settings()
    log = setup_logging()
    engine = get_engine()
    df = _load_completed_rides(engine)
    log.info("Loaded %s completed rides for anomaly screening", len(df))

    frames = [
        rule_based_flags(df),
        zscore_flags(df, settings.anomaly_zscore_threshold),
    ]
    if settings.anomaly_isolation_forest:
        frames.append(isolation_forest_scores(df))

    nonempty = [f for f in frames if f is not None and not f.empty]
    combined = pd.concat(nonempty, ignore_index=True) if nonempty else pd.DataFrame()
    if not combined.empty:
        # Keep highest severity per ride_id
        sev_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        combined["_sev"] = combined["severity"].map(sev_order)
        combined = (
            combined.sort_values("_sev", ascending=False)
            .groupby("ride_id", as_index=False)
            .first()
            .drop(columns=["_sev"], errors="ignore")
        )

    n = persist_anomalies(engine, combined)
    log.info("Persisted %s potential anomalies to monitoring.ride_anomalies", n)
    return {"anomalies": n, "rides_scanned": len(df)}


@click.command()
def main() -> None:
    result = run_anomaly_detection()
    click.echo(result)


if __name__ == "__main__":
    main()
