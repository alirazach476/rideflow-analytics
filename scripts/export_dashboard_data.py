"""Export live warehouse/analytics metrics for the RideFlow BI dashboard."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _engine():
    try:
        from pgserver import get_server

        pgdata = ROOT / ".pgdata"
        if pgdata.exists():
            server = get_server(pgdata, cleanup_mode=None)
            url = server.get_uri()
            return create_engine(url.replace("postgresql://", "postgresql+psycopg2://"))
    except Exception:
        pass
    from config.settings import get_settings

    return create_engine(get_settings().database_url)


def export(out: Path | None = None) -> Path:
    eng = _engine()

    def q(sql: str) -> pd.DataFrame:
        return pd.read_sql(text(sql), eng)

    kpis = q(
        """
        SELECT
          COUNT(*)::int AS total_rides,
          COUNT(*) FILTER (WHERE is_completed)::int AS completed_rides,
          COUNT(*) FILTER (WHERE is_cancelled)::int AS cancelled_rides,
          ROUND(100.0 * COUNT(*) FILTER (WHERE is_completed) / NULLIF(COUNT(*),0), 2)::float AS completion_rate,
          ROUND(100.0 * COUNT(*) FILTER (WHERE is_cancelled) / NULLIF(COUNT(*),0), 2)::float AS cancellation_rate,
          ROUND(SUM(total_fare) FILTER (WHERE is_completed)::numeric, 2)::float AS total_revenue,
          ROUND(AVG(total_fare) FILTER (WHERE is_completed)::numeric, 2)::float AS average_fare,
          ROUND(AVG(distance_km) FILTER (WHERE is_completed)::numeric, 2)::float AS average_distance,
          ROUND(AVG(duration_minutes) FILTER (WHERE is_completed)::numeric, 2)::float AS average_duration,
          COUNT(DISTINCT CASE WHEN is_completed THEN user_id END)::int AS active_users,
          COUNT(DISTINCT CASE WHEN is_completed THEN driver_id END)::int AS active_drivers
        FROM warehouse.fact_rides
        """
    ).iloc[0].to_dict()

    daily = q(
        """
        SELECT d.full_date::text AS full_date, m.total_rides, m.completed_rides,
               m.total_revenue::float, m.average_fare::float, m.cancellation_rate::float
        FROM analytics.mart_daily_ride_metrics m
        JOIN warehouse.dim_date d ON m.date_key = d.date_key
        ORDER BY d.full_date
        """
    )
    if len(daily) > 120:
        daily = daily.iloc[:: max(1, len(daily) // 90)].reset_index(drop=True)

    payload = {
        "meta": {
            "company": "RideFlow",
            "source": "PostgreSQL warehouse + analytics marts",
            "note": "Synthetic data. Analytical anomaly monitoring is not fraud confirmation.",
        },
        "kpis": kpis,
        "cities": q(
            """SELECT city_name, total_rides, completed_rides, completion_rate::float,
                      cancellation_rate::float, total_revenue::float, average_fare::float,
                      average_surge::float
               FROM analytics.mart_city_performance ORDER BY total_revenue DESC NULLS LAST"""
        ).to_dict(orient="records"),
        "vehicles": q(
            """SELECT vehicle_type, total_rides, completed_rides, revenue::float,
                      average_fare::float, cancellation_rate::float
               FROM analytics.mart_vehicle_performance ORDER BY completed_rides DESC"""
        ).to_dict(orient="records"),
        "surge": q(
            """SELECT surge_multiplier::float, ride_demand, completed_rides, revenue::float,
                      average_fare::float, completion_rate::float, cancellation_rate::float
               FROM analytics.mart_surge_analysis ORDER BY surge_multiplier"""
        ).to_dict(orient="records"),
        "payments": q(
            """SELECT payment_method, payment_count, payment_value::float, success_rate::float,
                      failure_rate::float, method_share_pct::float
               FROM analytics.mart_payment_performance ORDER BY payment_count DESC"""
        ).to_dict(orient="records"),
        "daily": daily.to_dict(orient="records"),
        "hourly": q(
            """SELECT EXTRACT(HOUR FROM request_timestamp)::int AS hour,
                      COUNT(*)::int AS ride_requests,
                      COUNT(*) FILTER (WHERE is_completed)::int AS completed,
                      COUNT(*) FILTER (WHERE is_cancelled)::int AS cancelled
               FROM warehouse.fact_rides GROUP BY 1 ORDER BY 1"""
        ).to_dict(orient="records"),
        "zones": q(
            """SELECT zone_name, zone_type, pickup_volume, revenue::float,
                      average_fare::float, cancellation_rate::float
               FROM analytics.mart_zone_performance ORDER BY pickup_volume DESC LIMIT 15"""
        ).to_dict(orient="records"),
        "segments": q(
            """SELECT customer_segment, COUNT(*)::int AS users,
                      ROUND(SUM(total_spend)::numeric,2)::float AS spend
               FROM analytics.mart_user_activity GROUP BY 1 ORDER BY spend DESC NULLS LAST"""
        ).to_dict(orient="records"),
        "drivers": q(
            """SELECT driver_id, driver_type, completed_rides, average_rating::float,
                      revenue_generated::float, revenue_per_online_hour::float,
                      rides_per_online_hour::float, cancellation_rate::float
               FROM analytics.mart_driver_performance
               WHERE online_hours > 0
               ORDER BY revenue_per_online_hour DESC NULLS LAST LIMIT 15"""
        ).to_dict(orient="records"),
        "cancel_reasons": q(
            """SELECT COALESCE(cancelled_by,'Unknown') AS cancelled_by,
                      COALESCE(cancellation_reason,'Unspecified') AS reason,
                      SUM(cancellations)::int AS total
               FROM analytics.mart_cancellation_analysis
               GROUP BY 1,2 ORDER BY total DESC LIMIT 20"""
        ).to_dict(orient="records"),
        "cancel_hour": q(
            """SELECT hour_of_day, SUM(cancellations)::int AS cancellations
               FROM analytics.mart_cancellation_analysis GROUP BY 1 ORDER BY 1"""
        ).to_dict(orient="records"),
        "status_dist": q(
            """SELECT ride_status, COUNT(*)::int AS n
               FROM warehouse.fact_rides GROUP BY 1 ORDER BY n DESC"""
        ).to_dict(orient="records"),
        "anomalies": q(
            """SELECT severity, COUNT(*)::int AS n
               FROM monitoring.ride_anomalies GROUP BY 1"""
        ).to_dict(orient="records"),
        "anomaly_reasons": q(
            """SELECT LEFT(anomaly_reason, 80) AS reason, severity, COUNT(*)::int AS n
               FROM monitoring.ride_anomalies GROUP BY 1,2 ORDER BY n DESC LIMIT 10"""
        ).to_dict(orient="records"),
        "supply": q(
            """SELECT demand_pressure_band, COUNT(*)::int AS buckets,
                      ROUND(AVG(demand_supply_ratio)::numeric,3)::float AS avg_ratio
               FROM analytics.mart_supply_demand GROUP BY 1 ORDER BY buckets DESC"""
        ).to_dict(orient="records"),
        "monthly": q(
            """SELECT year, month, month_name, total_rides, completed_rides,
                      total_revenue::float, average_fare::float, revenue_growth_mom::float
               FROM analytics.mart_monthly_ride_metrics ORDER BY year, month"""
        ).to_dict(orient="records"),
        "ratings": q(
            """SELECT rated_entity, rating_count, average_rating::float,
                      excellent, good, average, poor, very_poor
               FROM analytics.mart_rating_analysis"""
        ).to_dict(orient="records"),
    }

    def _clean(obj):
        if isinstance(obj, float) and (obj != obj):  # NaN
            return None
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_clean(v) for v in obj]
        return obj

    payload = _clean(payload)

    out = out or (ROOT / "dashboards" / "rideflow_dashboard_data.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, default=str), encoding="utf-8")

    # Also inject into HTML dashboard if present
    html_path = ROOT / "dashboards" / "rideflow_bi_dashboard.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8")
        marker_start = "/*__RIDEFLOW_DATA_START__*/"
        marker_end = "/*__RIDEFLOW_DATA_END__*/"
        if marker_start in html and marker_end in html:
            before = html.split(marker_start)[0]
            after = html.split(marker_end)[1]
            injected = (
                before
                + marker_start
                + "\nconst RIDEFLOW_DATA = "
                + json.dumps(payload, default=str)
                + ";\n"
                + marker_end
                + after
            )
            html_path.write_text(injected, encoding="utf-8")

    return out


if __name__ == "__main__":
    path = export()
    print(f"Exported {path}")
