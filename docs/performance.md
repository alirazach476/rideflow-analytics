# RideFlow Performance Optimization

Performance guidance for the **local PostgreSQL** analytics workload. No fabricated benchmark numbers — run `EXPLAIN ANALYZE` on your machine after scaling data.

---

## Index Strategy

File: `sql/performance/indexes.sql`

Indexes are created only where query patterns justify them.

### Raw Layer

| Index | Column(s) | Purpose |
|-------|-----------|---------|
| idx_raw_rides_request_ts | request_timestamp | Time-range scans |
| idx_raw_rides_user | user_id | User-centric queries |
| idx_raw_rides_driver | driver_id | Driver lookups |
| idx_raw_rides_city | city_id | City filters |
| idx_raw_rides_pickup_zone | pickup_zone_id | Geo analytics |
| idx_raw_rides_dropoff_zone | dropoff_zone_id | OD routes |
| idx_raw_payments_ride | ride_id | Payment joins |
| idx_raw_sessions_driver | driver_id | Supply analytics |

### Warehouse Layer

Apply after `dbt build`:

| Index | Column(s) | Purpose |
|-------|-----------|---------|
| idx_fact_rides_date | date_key | Daily aggregations |
| idx_fact_rides_city | city_id | City mart builds |
| idx_fact_rides_user | user_id | Customer analytics |
| idx_fact_rides_driver | driver_id | Driver analytics |
| idx_fact_rides_status | is_completed, is_cancelled | KPI filters |
| idx_fact_payments_method | payment_method | Payment breakdown |
| idx_fact_sessions_driver | driver_id | Utilization |

Run manually post-build:

```bash
psql -h localhost -U rideflow -d rideflow -f sql/performance/indexes.sql
```

---

## Query Analysis

File: `sql/performance/explain_examples.sql`

Use PostgreSQL planner tools:

```sql
EXPLAIN SELECT ...;
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT ...;
```

### Example patterns to analyze

1. Daily revenue aggregation on `fact_rides` by `date_key`
2. City performance join (`fact_rides` ⋈ `dim_city`)
3. Top drivers by revenue (window + rank)
4. Hourly supply-demand from `fact_driver_sessions`

Look for: sequential scans on large tables, nested loop on high-cardinality joins, sort spills to disk.

---

## Optimization Techniques

### Applied in RideFlow

| Technique | Where |
|-----------|-------|
| Surrogate keys (MD5) | Warehouse joins |
| Pre-aggregated marts | `analytics.*` — BI reads marts not raw |
| Partial filters | `FILTER (WHERE is_completed)` in SQL |
| Batch ingestion | `chunksize=2000` in pandas to_sql |
| Dedupe before load | Reduces raw table bloat |

### Recommended at Scale

| Technique | When |
|-----------|------|
| **Partitioning** `fact_rides` by month | > 10M rows |
| **BRIN** on request_timestamp | Append-only time series |
| **Materialized views** | Heavy repeated dashboards |
| **Connection pooling** | Multiple BI users |
| **ANALYZE** after large loads | Stale statistics |

### Partitioning Discussion

For 3M+ rides, range partition by `request_timestamp` month:

```sql
-- Conceptual — not applied in default setup
CREATE TABLE warehouse.fact_rides_2024_06
    PARTITION OF warehouse.fact_rides
    FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');
```

Benefits: partition pruning on date filters, faster VACUUM, easier archival.

---

## dbt Materialization Choices

| Layer | Materialization | Rationale |
|-------|-----------------|-----------|
| staging | view | Always fresh from raw |
| warehouse | table | Stable join target for BI |
| analytics | table | Fast dashboard queries |

---

## Ingestion Performance

| Setting | Default | Notes |
|---------|---------|-------|
| BATCH_SIZE | 10,000 | Env configurable |
| chunksize (to_sql) | 2,000 | Memory vs speed tradeoff |
| Incremental delete chunks | 5,000 IDs | Avoids large ANY() arrays |

Full truncate + reload is faster for dev volumes; incremental preferred for large production-style datasets.

---

## Anomaly Detection Performance

Rule-based and z-score loops iterate in pandas — acceptable for 100K rides. At millions:

- Push percentile calculations to SQL
- Sample for Isolation Forest training
- Run anomaly detection on daily partition only

---

## Power BI Performance

- Import **analytics marts** instead of fact_rides detail
- Hide unused columns and surrogate keys
- Use aggregations at source (SQL) not DAX where possible

---

## Monitoring Checklist

After scaling data, measure:

1. `make pipeline` total duration
2. dbt model run times (`target/run_results.json`)
3. Top 5 slow queries via `EXPLAIN ANALYZE`
4. Index usage: `pg_stat_user_indexes`

Document your results locally — do not commit fabricated timings.

---

## Anti-Patterns to Avoid

- Selecting `SELECT *` from raw.rides in dashboards
- Missing indexes on join keys (user_id, date_key)
- Running Isolation Forest on full history every hour
- Creating indexes on every column without query justification
