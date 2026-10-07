"""Intentionally inject a small number of realistic data-quality issues."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

import numpy as np


def inject_quality_issues(
    datasets: Dict[str, List[Dict[str, Any]]],
    rate: float = 0.002,
    seed: int = 42,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Inject controlled DQ issues into a copy of the datasets.

    Issues include: duplicates, missing FKs, invalid statuses, bad timestamps,
    negative discounts, zero distances, capitalization inconsistency, fare mismatches.
    """
    rng = np.random.default_rng(seed + 7)
    data = {k: deepcopy(v) for k, v in datasets.items()}

    users = data["users"]
    rides = data["rides"]
    payments = data["payments"]

    n_dup_users = max(1, int(len(users) * rate * 0.5))
    n_dup_rides = max(1, int(len(rides) * rate * 0.5))
    n_bad = max(5, int(len(rides) * rate))

    # Duplicate users (same user_id)
    for _ in range(n_dup_users):
        if users:
            users.append(deepcopy(users[int(rng.integers(0, len(users)))]))

    # Duplicate rides
    for _ in range(n_dup_rides):
        if rides:
            rides.append(deepcopy(rides[int(rng.integers(0, len(rides)))]))

    # Duplicate payments
    for _ in range(max(1, n_dup_rides // 2)):
        if payments:
            payments.append(deepcopy(payments[int(rng.integers(0, len(payments)))]))

    # Corrupt a sample of rides
    if rides:
        idxs = rng.choice(len(rides), size=min(n_bad, len(rides)), replace=False)
        for i, idx in enumerate(idxs):
            ride = rides[int(idx)]
            issue = i % 10
            if issue == 0:
                ride["driver_id"] = None  # missing driver on completed-looking ride
                if ride.get("ride_status") == "Completed":
                    ride["ride_status"] = "Completed"
            elif issue == 1:
                ride["pickup_zone_id"] = None
            elif issue == 2:
                ride["ride_status"] = "completED"  # capitalization
            elif issue == 3:
                ride["ride_status"] = "Flying"  # invalid status
            elif issue == 4 and ride.get("total_fare") is not None:
                ride["discount_amount"] = -25.0
            elif issue == 5 and ride.get("distance_km"):
                ride["distance_km"] = 0.0
            elif issue == 6 and ride.get("duration_minutes"):
                ride["duration_minutes"] = -10.0
            elif issue == 7 and ride.get("request_timestamp") and ride.get("dropoff_timestamp"):
                # swap timestamps — impossible sequence
                ride["request_timestamp"], ride["dropoff_timestamp"] = (
                    ride["dropoff_timestamp"],
                    ride["request_timestamp"],
                )
            elif issue == 8 and ride.get("total_fare") is not None:
                ride["total_fare"] = round(float(ride["total_fare"]) * 1.5, 2)  # fare mismatch
            elif issue == 9:
                ride["user_id"] = 99_999_999  # invalid FK

    # Invalid payment statuses
    if payments:
        for idx in rng.choice(len(payments), size=min(3, len(payments)), replace=False):
            payments[int(idx)]["payment_status"] = "Unknown"

    data["users"] = users
    data["rides"] = rides
    data["payments"] = payments
    return data
