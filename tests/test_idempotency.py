"""Idempotency helpers — dedupe logic used by ingestion."""

from __future__ import annotations

import pandas as pd

from src.ingestion.load_raw import _dedupe


def test_dedupe_keeps_last():
    df = pd.DataFrame(
        [
            {"ride_id": 1, "total_fare": 10, "batch": "a"},
            {"ride_id": 1, "total_fare": 20, "batch": "b"},
            {"ride_id": 2, "total_fare": 30, "batch": "a"},
        ]
    )
    out = _dedupe(df, ["ride_id"])
    assert len(out) == 2
    assert int(out.loc[out["ride_id"] == 1, "total_fare"].iloc[0]) == 20
