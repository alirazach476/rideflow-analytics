"""Pricing and anomaly unit tests."""

from __future__ import annotations

import pandas as pd

from config.pricing import TAX_RATE, VEHICLE_PRICING, calculate_fare
from src.anomaly_detection.detect import rule_based_flags, zscore_flags


def test_fare_components_match_formula():
    v = "Sedan"
    dist, dur, surge = 10.0, 20.0, 1.2
    toll, disc = 50.0, 20.0
    fare = calculate_fare(v, dist, dur, surge, toll, disc)
    p = VEHICLE_PRICING[v]
    subtotal = (p["base_fare"] + dist * p["price_per_km"] + dur * p["price_per_minute"] + p["booking_fee"] + toll) * surge
    tax = round(subtotal * TAX_RATE, 2)
    expected = max(0.0, round(subtotal - disc + tax, 2))
    assert abs(fare["total_fare"] - expected) < 0.01


def test_rule_based_flags_high_fare():
    df = pd.DataFrame(
        [
            {"ride_id": i, "user_id": 1, "driver_id": 1, "ts": f"2024-06-01 12:{i:02d}:00",
             "fare": 100 + i, "distance_km": 5, "duration_minutes": 15, "surge_multiplier": 1.0, "city_id": 1, "ride_status": "Completed"}
            for i in range(20)
        ]
        + [
            {"ride_id": 999, "user_id": 1, "driver_id": 1, "ts": "2024-06-01 13:00:00",
             "fare": 5000, "distance_km": 5, "duration_minutes": 15, "surge_multiplier": 1.0, "city_id": 1, "ride_status": "Completed"}
        ]
    )
    flags = rule_based_flags(df)
    assert not flags.empty
    assert 999 in set(flags["ride_id"])


def test_zscore_detection():
    rows = [{"ride_id": i, "user_id": 7, "driver_id": 1, "ts": f"2024-01-01 10:00:{i:02d}",
             "fare": 100.0, "distance_km": 5, "duration_minutes": 10, "surge_multiplier": 1.0,
             "city_id": 1, "ride_status": "Completed"} for i in range(10)]
    rows.append({"ride_id": 100, "user_id": 7, "driver_id": 1, "ts": "2024-01-01 11:00:00",
                 "fare": 1000.0, "distance_km": 5, "duration_minutes": 10, "surge_multiplier": 1.0,
                 "city_id": 1, "ride_status": "Completed"})
    df = pd.DataFrame(rows)
    flags = zscore_flags(df, threshold=3.0)
    assert not flags.empty
    assert 100 in set(flags["ride_id"])
