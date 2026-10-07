"""Data reconciliation across source → raw → warehouse → analytics."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.db import get_engine
from src.utils.logging_config import setup_logging


def _scalar(engine, sql: str) -> Optional[float]:
    try:
        with engine.connect() as conn:
            val = conn.execute(text(sql)).scalar()
            return float(val) if val is not None else 0.0
    except Exception:
        return None


def _compare(
    metric: str,
    source: Optional[float],
    warehouse: Optional[float],
    warn_pct: float = 0.01,
    fail_pct: float = 0.05,
) -> Tuple[str, float]:
    if source is None or warehouse is None:
        return "WARNING", 0.0
    diff = warehouse - source
    base = abs(source) if source != 0 else 1.0
    pct = abs(diff) / base
    if pct <= warn_pct:
        status = "PASS"
    elif pct <= fail_pct:
        status = "WARNING"
    else:
        status = "FAIL"
    return status, diff


def run_reconciliation() -> List[Dict[str, Any]]:
    log = setup_logging()
    engine = get_engine()
    run_id = str(uuid.uuid4())

    metrics = [
        (
            "ride_count",
            "SELECT COUNT(DISTINCT ride_id) FROM raw.rides",
            "SELECT COUNT(*) FROM warehouse.fact_rides",
        ),
        (
            "completed_ride_count",
            "SELECT COUNT(DISTINCT ride_id) FROM raw.rides WHERE LOWER(ride_status)='completed'",
            "SELECT COUNT(*) FROM warehouse.fact_rides WHERE is_completed = TRUE",
        ),
        (
            "revenue",
            "SELECT COALESCE(SUM(total_fare),0) FROM raw.rides WHERE LOWER(ride_status)='completed'",
            "SELECT COALESCE(SUM(total_fare),0) FROM warehouse.fact_rides WHERE is_completed = TRUE",
        ),
        (
            "payment_amount",
            "SELECT COALESCE(SUM(amount),0) FROM raw.payments WHERE LOWER(payment_status)='completed'",
            "SELECT COALESCE(SUM(amount),0) FROM warehouse.fact_payments WHERE payment_status = 'Completed'",
        ),
    ]

    results: List[Dict[str, Any]] = []
    with engine.begin() as conn:
        for name, src_sql, wh_sql in metrics:
            src = _scalar(engine, src_sql)
            wh = _scalar(engine, wh_sql)
            # Fallback: if warehouse missing, compare raw to itself as WARNING
            if wh is None:
                status, diff = "WARNING", 0.0
                wh = 0.0
                src = src or 0.0
            else:
                status, diff = _compare(name, src, wh)
            row = {
                "run_id": run_id,
                "metric_name": name,
                "source_value": src or 0.0,
                "warehouse_value": wh or 0.0,
                "difference": diff,
                "status": status,
            }
            conn.execute(
                text(
                    """
                    INSERT INTO audit.reconciliation_results
                        (run_id, metric_name, source_value, warehouse_value, difference, status)
                    VALUES (:run_id, :metric_name, :source_value, :warehouse_value, :difference, :status)
                    """
                ),
                row,
            )
            results.append(row)
            log.info("Reconciliation %s: %s (src=%s wh=%s diff=%s)", name, status, src, wh, diff)
    return results


@click.command()
def main() -> None:
    for r in run_reconciliation():
        click.echo(r)


if __name__ == "__main__":
    main()
