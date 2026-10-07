# RideFlow — Final Project Report

Comprehensive summary of the Ride-Hailing Analytics Platform. All metrics and insights referenced here should be verified by running `make pipeline` against your local dataset — numbers are not pre-populated.

---

## 1. Project Overview

**RideFlow** is a fictional ride-hailing company's analytics platform built as a local, batch-oriented data engineering and analytics project. It generates 100% synthetic data, loads PostgreSQL, transforms with dbt, orchestrates with Airflow, screens for ride anomalies, and prepares Power BI dashboards.

**Scope:** Demonstrate DE + analytics + BI skills without cloud dependencies, real-time streaming, or fraud detection claims.

---

## 2. Business Problem

Ride-hailing operators need unified analytics to answer questions about ride volume, revenue, geographic demand, surge impact, cancellations, driver performance, customer value, supply gaps, and unusual patterns requiring review. RideFlow builds the warehouse and marts to support these decisions.

---

## 3. Architecture

Local ELT pipeline:

```text
Synthetic Sources → CSV → Validation → Python Ingest → PostgreSQL (raw)
  → dbt (staging → warehouse → analytics) → Reconciliation → Anomaly Screening
  → Airflow orchestration → Power BI
```

See [architecture.md](architecture.md) for Mermaid diagrams.

---

## 4. Synthetic Data Generation

Python modules in `src/data_generation/` use Faker, numpy, and documented pricing rules to create realistic ride-hailing behavior:

- User type affects ride frequency and vehicle preference
- Surge tied to hour, zone demand, and peak periods
- Status distribution: ~72% completed, ~12% rider cancel, ~8% driver cancel
- Pakistani-inspired cities (Lahore, Karachi, Islamabad, etc.)

Default dev sizes: 10K users, 100K rides (configurable to 3M+ via `.env`).

---

## 5. Source Systems

Fictional platform exports simulated as CSV:

| System | File |
|--------|------|
| User Platform | users.csv |
| Driver Platform | drivers.csv, vehicles.csv, driver_sessions.csv |
| Ride Platform | rides.csv |
| Payment Platform | payments.csv |
| Rating Platform | ratings.csv |
| Promotion Platform | promotions.csv |
| Geo Reference | cities.csv, zones.csv |

---

## 6. Data Quality

Pre-load framework (`src/validation/checks.py`): null, uniqueness, referential, numeric, timestamp, fare reconciliation, status validation. ~0.2% intentional issues injected for realism. Results: `data/processed/dq_results.json`. dbt tests on staging models.

---

## 7. PostgreSQL Architecture

Six schemas: `raw`, `staging`, `warehouse`, `analytics`, `audit`, `monitoring`. Docker Compose Postgres 16 with init DDL mounted at startup.

---

## 8. Star Schema

Dimensions: user (SCD2), driver, vehicle, city, zone, date, time, payment_method, ride_status, promotion.  
Facts: rides, payments, driver_sessions, ratings.

---

## 9. Fact Table Grain

**`fact_rides`: One row represents one ride request/event.**

All ride statuses included. Revenue metrics filter to `is_completed = TRUE`.

---

## 10. SCD Type 2

`dim_user` includes `effective_date`, `expiration_date`, `is_current`. Initial load creates one current version per user. Infrastructure supports historical versions on attribute changes via `dbt/macros/scd_type2.sql`.

---

## 11. Incremental Processing

`load_raw.py --mode incremental` filters by watermark timestamps stored in `audit.pipeline_watermarks`. Deletes existing keys before append for upsert semantics.

---

## 12. Idempotency

Natural-key dedupe, truncate (full) or delete+append (incremental), dbt table replacement, anomaly table truncate-reload. Verified by `tests/test_idempotency.py`.

---

## 13. dbt Transformations

dbt project `rideflow`: staging views → intermediate fare components → warehouse tables → 14 analytics marts. Command: `make dbt-build`.

---

## 14. Airflow Orchestration

DAG `rideflow_daily_pipeline`: check sources → generate → validate → load → dbt layers → reconcile → anomaly → dbt test → audit. Schedule `@daily`. Docker Compose provides webserver + scheduler.

---

## 15. Advanced SQL

30+ queries in `sql/analytics/` covering JOINs, CTEs, window functions (ROW_NUMBER, RANK, LAG, rolling averages), cohort analysis, geo/surge/cancel patterns.

---

## 16. Customer Analytics

`mart_user_activity`, `mart_cohort_retention`: segments (Inactive through Premium), retention windows, spend and ride frequency per user.

---

## 17. Driver Analytics

`mart_driver_performance`: rides, revenue, ratings, cancellation, ranking via window functions. Sessions enable utilization metrics.

---

## 18. Supply-Demand Analytics

`mart_supply_demand`: hourly ride requests vs driver availability, demand/supply ratio with documented pressure thresholds.

---

## 19. Surge Analytics

`mart_surge_analysis`: surge multiplier vs revenue, completion, cancellation — empirically computed, not assumed.

---

## 20. Cancellation Analytics

`mart_cancellation_analysis`: rider vs driver cancels by city, hour, vehicle, surge, reason categories.

---

## 21. Anomaly Detection

Rule-based + z-score + optional Isolation Forest. Output: `monitoring.ride_anomalies`. **Screening only — not fraud confirmation.**

---

## 22. Power BI

Specification: 9 dashboard pages, star-schema relationships, DAX measures documented. Connect Desktop to PostgreSQL. No bundled `.pbix` — build locally from spec.

---

## 23. Business Insights

Must be SQL-generated. Template: `analysis/business_insights.md`. Run `make pipeline` then `python scripts/generate_insights.py`. Do not invent numbers in documentation.

---

## 24. Testing

pytest suite: data generation, validation, pricing, idempotency, anomaly logic. Command: `make test`.

---

## 25. Performance

Indexes in `sql/performance/indexes.sql`. EXPLAIN examples provided. Partitioning discussed for 10M+ scale. No fabricated benchmark results.

---

## 26. Limitations

- Local batch only; no real-time streaming
- Default dataset smaller than brief's 3M ride target
- SCD Type 2 merge not fully exercised on incremental user changes
- Per-entity Airflow ingest tasks are placeholders
- DQ results not yet persisted to `audit.data_quality_results` table
- Anomaly detection uses pandas loops — not production-scale
- Power BI dashboard is spec-only until built locally
- No cloud deployment included

---

## 27. Future Improvements

- Scale to 3M+ rides; benchmark with EXPLAIN ANALYZE
- Full SCD2 incremental pipeline for users
- Persist DQ to audit schema; Great Expectations integration
- Monthly partitioning on fact_rides
- CI/CD (GitHub Actions): pytest + dbt
- Export `.pbix` template
- Push anomaly scoring to SQL for scale

---

## 28. Cloud Architecture

Conceptual migration paths to AWS (S3/Glue/Redshift/MWAA), Azure (ADLS/ADF/Synapse), GCP (GCS/Dataflow/BigQuery/Composer). See [cloud_architecture.md](cloud_architecture.md). Migration is infrastructure swap — star schema and dbt logic largely portable.

---

## How to Reproduce

```bash
make setup
make pipeline
make test
python scripts/generate_insights.py
```

Airflow: `docker compose up -d` → trigger `rideflow_daily_pipeline`.

Power BI: connect to `localhost:5432`, database `rideflow`, schemas `warehouse` + `analytics`.

---

*Report generated as project documentation. Verify all quantitative claims against your pipeline run.*
