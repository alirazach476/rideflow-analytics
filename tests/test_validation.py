"""Tests for data quality framework."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.validation.checks import DataQualityFramework


def test_detects_duplicate_users(tmp_path: Path):
    src = tmp_path / "user_platform"
    src.mkdir()
    df = pd.DataFrame(
        [
            {"user_id": 1, "registration_date": "2024-01-01", "city_id": 1, "user_type": "Regular", "status": "Active"},
            {"user_id": 1, "registration_date": "2024-01-01", "city_id": 1, "user_type": "Regular", "status": "Active"},
            {"user_id": 2, "registration_date": "2024-01-02", "city_id": 1, "user_type": "Student", "status": "Active"},
        ]
    )
    df.to_csv(src / "users.csv", index=False)
    # minimal other tables so framework loads
    for name, cols in {
        "drivers": ["driver_id", "registration_date", "city_id", "status", "rating"],
        "vehicles": ["vehicle_id", "driver_id", "vehicle_type", "status"],
        "rides": ["ride_id", "user_id", "city_id", "request_timestamp", "ride_status", "driver_id", "vehicle_id", "surge_multiplier"],
        "payments": ["payment_id", "ride_id", "user_id", "amount", "payment_status"],
    }.items():
        p = tmp_path / "other"
        p.mkdir(exist_ok=True)
        empty = pd.DataFrame({c: [] for c in cols})
        # put rides etc in nested folders matching glob
        (tmp_path / "ride_platform").mkdir(exist_ok=True)
        (tmp_path / "driver_platform").mkdir(exist_ok=True)
        (tmp_path / "payment_platform").mkdir(exist_ok=True)

    pd.DataFrame(
        [{"driver_id": 1, "registration_date": "2024-01-01", "city_id": 1, "status": "Active", "rating": 4.5}]
    ).to_csv(tmp_path / "driver_platform" / "drivers.csv", index=False)
    pd.DataFrame(
        [{"vehicle_id": 1, "driver_id": 1, "vehicle_type": "Economy", "status": "Active"}]
    ).to_csv(tmp_path / "driver_platform" / "vehicles.csv", index=False)
    pd.DataFrame(
        [
            {
                "ride_id": 1,
                "user_id": 1,
                "city_id": 1,
                "request_timestamp": "2024-01-01 10:00:00",
                "ride_status": "Completed",
                "driver_id": 1,
                "vehicle_id": 1,
                "surge_multiplier": 1.0,
                "distance_km": 5,
                "duration_minutes": 12,
                "total_fare": 100,
                "accepted_timestamp": "2024-01-01 10:01:00",
                "pickup_timestamp": "2024-01-01 10:05:00",
                "dropoff_timestamp": "2024-01-01 10:20:00",
                "base_fare": 50,
                "booking_fee": 10,
                "toll_amount": 0,
                "discount_amount": 0,
                "tax_amount": 5,
            }
        ]
    ).to_csv(tmp_path / "ride_platform" / "rides.csv", index=False)
    pd.DataFrame(
        [{"payment_id": 1, "ride_id": 1, "user_id": 1, "amount": 100, "payment_status": "Completed"}]
    ).to_csv(tmp_path / "payment_platform" / "payments.csv", index=False)

    fw = DataQualityFramework(data_dir=tmp_path)
    fw.run_all()
    uniq = [r for r in fw.results if r.check_name == "unique_user_id"]
    assert uniq and uniq[0].status == "FAIL"
    assert uniq[0].actual == 1


def test_invalid_rating_detected(tmp_path: Path):
    (tmp_path / "rating_platform").mkdir()
    pd.DataFrame(
        [{"rating_id": 1, "ride_id": 1, "user_id": 1, "driver_id": 1, "rating": 9, "rating_from": "User", "rating_to": "Driver"}]
    ).to_csv(tmp_path / "rating_platform" / "ratings.csv", index=False)
    # minimal rides/users to allow other checks
    (tmp_path / "user_platform").mkdir()
    pd.DataFrame(
        [{"user_id": 1, "registration_date": "2024-01-01", "city_id": 1, "user_type": "Regular", "status": "Active"}]
    ).to_csv(tmp_path / "user_platform" / "users.csv", index=False)
    (tmp_path / "ride_platform").mkdir()
    pd.DataFrame(
        [
            {
                "ride_id": 1,
                "user_id": 1,
                "city_id": 1,
                "request_timestamp": "2024-01-01 10:00:00",
                "ride_status": "Completed",
                "surge_multiplier": 1.0,
            }
        ]
    ).to_csv(tmp_path / "ride_platform" / "rides.csv", index=False)

    fw = DataQualityFramework(data_dir=tmp_path)
    fw.run_all()
    rating_checks = [r for r in fw.results if r.check_name == "rating_range"]
    assert rating_checks and rating_checks[0].status == "FAIL"
