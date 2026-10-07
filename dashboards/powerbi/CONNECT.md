# Connecting BI to RideFlow

## Option A — Interactive HTML dashboard (ready now)

Live warehouse metrics are rendered in:

`dashboards/rideflow_bi_dashboard.html`

Refresh from PostgreSQL and open:

```bash
python scripts/open_dashboard.py
# or
make dashboard
```

Pages: Executive, Rides, Customers, Drivers, City & Zones, Surge, Cancellations, Anomaly Monitor.

## Option B — Power BI Desktop

1. Ensure PostgreSQL is running (`make pipeline-local` or `docker compose up -d postgres`).
2. Get connection details from `.env` (or the ephemeral `pgserver` URI printed by the local pipeline).
3. Power BI → **Get Data** → **PostgreSQL database**
   - Server: `localhost` (and port if non-default)
   - Database: `rideflow` (or `postgres` for pgserver)
4. Import these tables/views:
   - `analytics.mart_*`
   - `warehouse.fact_rides`, `warehouse.dim_*`
   - `monitoring.ride_anomalies`
5. Build relationships using the star schema in `docs/data_model.md`.
6. Paste measures from `dashboards/powerbi/dax_measures.md`.
7. Follow page layout in `dashboards/powerbi/dashboard_spec.md`.

> Note: `.pbix` is a proprietary binary; this repo ships the **data model + DAX + page specs** plus a fully working HTML BI dashboard connected to the same warehouse.
