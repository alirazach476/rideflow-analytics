"""Generate analysis/*.md insights from live warehouse queries. Never invent numbers."""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils.db import get_engine
from src.utils.logging_config import setup_logging


QUERIES = {
    "top_revenue_city": """
        SELECT city_name, total_revenue, cancellation_rate
        FROM analytics.mart_city_performance
        ORDER BY total_revenue DESC NULLS LAST LIMIT 1
    """,
    "highest_cancel_city": """
        SELECT city_name, cancellation_rate, total_revenue
        FROM analytics.mart_city_performance
        ORDER BY cancellation_rate DESC NULLS LAST LIMIT 1
    """,
    "busiest_hour": """
        SELECT EXTRACT(HOUR FROM request_timestamp)::INT AS hour, COUNT(*) AS rides
        FROM warehouse.fact_rides
        GROUP BY 1 ORDER BY rides DESC LIMIT 1
    """,
    "surge_vs_metrics": """
        SELECT surge_multiplier, revenue, completion_rate, cancellation_rate, ride_demand
        FROM analytics.mart_surge_analysis ORDER BY surge_multiplier
    """,
    "top_vehicle": """
        SELECT vehicle_type, completed_rides, revenue
        FROM analytics.mart_vehicle_performance
        ORDER BY completed_rides DESC NULLS LAST LIMIT 1
    """,
    "top_driver_util": """
        SELECT driver_id, revenue_per_online_hour, rides_per_online_hour
        FROM analytics.mart_driver_performance
        WHERE online_hours > 0
        ORDER BY revenue_per_online_hour DESC NULLS LAST LIMIT 5
    """,
    "segment_revenue": """
        SELECT customer_segment, COUNT(*) AS users, ROUND(SUM(total_spend)::NUMERIC,2) AS spend
        FROM analytics.mart_user_activity
        GROUP BY 1 ORDER BY spend DESC NULLS LAST
    """,
    "demand_pressure": """
        SELECT demand_pressure_band, COUNT(*) AS buckets
        FROM analytics.mart_supply_demand
        GROUP BY 1 ORDER BY buckets DESC
    """,
    "payment_failures": """
        SELECT payment_method, failure_rate, payment_count
        FROM analytics.mart_payment_performance
        ORDER BY failure_rate DESC NULLS LAST
    """,
    "anomaly_counts": """
        SELECT severity, COUNT(*) AS n
        FROM monitoring.ride_anomalies
        GROUP BY 1 ORDER BY n DESC
    """,
}


def _fetch(engine, sql: str):
    with engine.connect() as conn:
        return conn.execute(text(sql)).fetchall()


def main() -> None:
    log = setup_logging()
    engine = get_engine()
    lines = [
        "# RideFlow Business Insights",
        "",
        "Generated from the live PostgreSQL warehouse. Numbers are not invented.",
        "",
        "> Analytical anomaly counts are screening signals, not fraud confirmations.",
        "",
    ]
    for name, sql in QUERIES.items():
        try:
            rows = _fetch(engine, sql)
            lines.append(f"## {name.replace('_', ' ').title()}")
            lines.append("")
            lines.append("```")
            if not rows:
                lines.append("(no rows)")
            else:
                for r in rows:
                    lines.append(str(dict(r._mapping)))
            lines.append("```")
            lines.append("")
        except Exception as exc:
            log.warning("Query %s failed: %s", name, exc)
            lines.append(f"## {name}")
            lines.append(f"_Query unavailable: {exc}_")
            lines.append("")

    out = ROOT / "analysis" / "business_insights.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    log.info("Wrote %s", out)


if __name__ == "__main__":
    main()
