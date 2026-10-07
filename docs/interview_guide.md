# RideFlow Interview Guide

Questions and answers grounded in this project. Use for data engineering, analytics, and BI interviews.

---

## Data Engineering

### Why PostgreSQL?

PostgreSQL 16 provides ACID transactions, mature indexing, window functions, and schema support — ideal for a **local star-schema warehouse**. It runs in Docker with zero cloud cost, supports dbt natively, and connects directly to Power BI. At RideFlow scale (100K–3M rides), Postgres handles batch analytics without needing a separate OLAP engine.

### Why star schema?

Ride analytics are inherently dimensional: rides happen at a **time**, in a **city/zone**, by a **user**, with a **driver** and **vehicle**. Star schema optimizes BI tools (Power BI) with simple many-to-one joins and pre-defined grain. Fact tables hold metrics; dimensions hold descriptive attributes.

### Why fact/dimension tables?

Separates **what happened** (facts: fares, distances) from **who/where/when** (dimensions: user, city, date). Enables conformed dimensions across multiple facts (rides, payments, sessions) and prevents redundant denormalization in every query.

### What is grain?

Grain defines what one row represents. `fact_rides` grain = **one ride request/event**. All metrics on that table must be additive or semi-additive at that grain. Wrong grain causes double-counting (e.g., joining payments without careful aggregation).

### ETL vs ELT?

RideFlow uses **ELT**: extract CSV → load raw Postgres → transform with dbt in-database. ELT leverages Postgres compute, keeps raw immutable, and lets dbt manage transformations as versioned SQL.

### Batch vs streaming?

RideFlow is **batch** (`@daily` Airflow schedule, full/incremental loads). Ride-hailing reporting (daily KPIs, marts) fits batch. Streaming would be needed for live driver dispatch — out of scope for this analytics platform.

### What is idempotency?

Re-running the pipeline produces the same result — no duplicate rides. Achieved via truncate+reload (full), delete-by-key+append (incremental), dedupe on natural keys, and dbt table materializations.

### What is incremental loading?

Loading only new/changed records since last watermark. RideFlow filters CSV rows where `updated_at` or event timestamp > `audit.pipeline_watermarks.watermark_ts`.

### What is a watermark?

A high-water mark timestamp stored per `(pipeline_name, table_name)` tracking the latest processed change. Enables incremental batches without reprocessing full history.

### Why use dbt?

dbt provides modular SQL transformations, dependency graph, testing (`not_null`, `unique`), documentation, and repeatable builds. Analytics engineers can own warehouse logic without Python glue code.

### Why use Airflow?

Airflow orchestrates multi-step batch pipelines with scheduling, retries, dependency management, and observability. RideFlow's DAG coordinates generation, validation, ingest, dbt, reconciliation, and anomaly screening.

---

## SQL

### CTE (Common Table Expression)

Readable subqueries with `WITH`. Used throughout `sql/analytics/` for multi-step KPI calculations.

```sql
WITH completed AS (
    SELECT * FROM warehouse.fact_rides WHERE is_completed
)
SELECT city_id, SUM(total_fare) FROM completed GROUP BY 1;
```

### Window functions

Compute across rows without collapsing groups. RideFlow uses:

| Function | Use case |
|----------|----------|
| ROW_NUMBER() | Top-N drivers per city |
| RANK() / DENSE_RANK() | Revenue leaderboards |
| LAG() / LEAD() | MoM revenue comparison |
| SUM() OVER() | Running cumulative revenue |
| AVG() OVER() | 7-day rolling ride average |

### JOIN types

- **INNER JOIN**: Matching rows only (rides with valid city)
- **LEFT JOIN**: All rides including missing driver (cancelled early)
- Used in fact_rides build and analytics queries

### GROUP BY / HAVING

GROUP BY aggregates; HAVING filters groups (e.g., cities with > 1000 rides).

### Conditional aggregation

PostgreSQL `COUNT(*) FILTER (WHERE condition)` for completion/cancellation rates without multiple subqueries.

---

## Analytics

### Completion rate

`Completed Rides / Total Rides`. Key health metric. RideFlow ~72% completed in synthetic distribution.

### Cancellation rate

`Cancelled Rides / Total Rides`. Split by rider vs driver for root-cause analysis.

### Customer retention

Track cohorts by signup month; measure % returning within 30/60/90 days. Implemented in `mart_cohort_retention`.

### Driver utilization

`completed_rides / online_hours` from sessions + rides. Identifies under-utilized supply.

### Supply-demand ratio

`ride_requests / available_drivers` by hour/city. Values > 1.5 indicate pressure; informs surge decisions.

### Surge pricing

Multiplier applied to fare subtotal during peak demand. Analyze correlation with revenue AND cancellation — don't assume direction; compute from data.

---

## Data Quality

### Duplicate records

Injected intentionally; detected by uniqueness checks; resolved by ingest dedupe (`keep='last'`).

### Null values

Required fields checked pre-load. Nullable FKs (driver_id on early-stage rides) handled in staging.

### Referential integrity

rides.user_id must exist in users. Validation fails on orphan keys unless filtered in staging.

### Reconciliation

Post-transform comparison of counts and revenue between raw and warehouse. PASS/WARNING/FAIL thresholds at 1%/5%.

---

## ML / Anomaly

### Isolation Forest

Unsupervised algorithm isolating outliers in feature space. Used optionally for ride screening with features like fare, distance, hour. `contamination=0.01` expects ~1% outliers.

### Z-score

Standardizes fare vs customer's historical mean. Flags rides > 3σ — configurable threshold.

### Feature engineering

Derived: `hour_of_day`, `rides_last_1_hour`, `fare_vs_user_average`. Captures behavioral context beyond raw fare.

### False positives

Screening will flag legitimate edge cases (airport rides, premium users). Requires human review — not auto-block.

### Anomaly vs fraud

**Anomaly** = statistical or rule-based unusual pattern. **Fraud** = confirmed malicious intent requiring investigation, evidence, and policy action. RideFlow does anomaly screening only.

---

## Power BI

### Measures vs calculated columns

Measures aggregate dynamically (Total Revenue). Calculated columns are row-level and static at refresh — prefer measures for KPIs.

### Relationships

Star schema: many fact rows to one dimension row. Active relationship on date_key, city_key, etc. Hide surrogate keys from report view.

### Filter context

Slicers (Date, City) filter all measures simultaneously. Understand `CALCULATE` for overriding filters.

### DAX

Data Analysis Expressions for measures. See `dashboards/powerbi/dax_measures.md`. Example:

```dax
Completion Rate = DIVIDE ( [Completed Rides], [Total Rides] )
```

### Star schema in Power BI

Import fact + dimensions; avoid snowflaking in the model unless necessary. Use marts for heavy aggregations.

---

## Scenario Questions

**"How would you add a new city?"**  
Generate in data layer → flows through CSV → raw → staging → dim_city → facts auto-join on city_id.

**"Pipeline ran twice — what happens?"**  
Idempotent: full mode truncates; incremental upserts by key; dbt replaces tables; anomalies truncate-reload.

**"How do you know data is trustworthy?"**  
Pre-load validation + dbt tests + reconciliation + audit.pipeline_runs logging.

**"Why not put everything in one wide table?"**  
Violates normalization, duplicates dimension attributes, breaks BI relationships, and complicates SCD history.

---

## Quick Project Talking Points

1. End-to-end local batch platform with synthetic Pakistani-inspired cities
2. Documented fare formula with DQ reconciliation
3. Star schema with explicit fact grain and SCD Type 2 user dimension
4. 14 analytics marts + 30+ SQL queries
5. Anomaly **screening** (not fraud) with rules + z-score + optional ML
6. Airflow DAG + Makefile for reproducibility
7. Honest about limitations — no cloud, no streaming, no fabricated insights
