# RideFlow Pipeline

The RideFlow pipeline is a **local batch ELT** process. It does not use real-time streaming or cloud-managed orchestration by default.

---

## Pipeline Stages

| Stage | Component | Command / Location |
|-------|-----------|-------------------|
| 1. Generate | `src/data_generation/generate.py` | `make generate-data` |
| 2. Validate | `src/validation/run_validation.py` | `make validate` |
| 3. Database | Docker Postgres | `make docker-up` |
| 4. Ingest | `src/ingestion/load_raw.py` | `make ingest` |
| 5. Transform | dbt | `make dbt-build` |
| 6. Anomaly | `src/anomaly_detection/detect.py` | `make anomaly-detection` |
| 7. Reconcile | `src/transformation/reconcile.py` | `make reconcile` |

**One command:** `make pipeline` runs stages 1–7 sequentially.

---

## Load Modes

### Full Load (default)

```bash
make ingest
# python -m src.ingestion.load_raw --mode full
```

Behavior:
1. `TRUNCATE` each `raw.*` table
2. Deduplicate CSV rows by natural key (`keep='last'`)
3. Append with `source_file`, `ingestion_timestamp`, `batch_id`
4. Update watermarks after successful load

Use for: initial load, development resets, full refresh.

### Incremental Load

```bash
make ingest-incremental
# python -m src.ingestion.load_raw --mode incremental
```

Behavior:
1. Read watermark from `audit.pipeline_watermarks`
2. Filter source rows where timestamp column > watermark
   - Priority columns: `updated_at`, `request_timestamp`, `payment_timestamp`, `rating_timestamp`, `session_start`
3. **Delete** existing raw rows matching incoming natural keys (chunked, 5000 IDs)
4. **Append** new/changed rows
5. Update watermark to `NOW()` (UTC)

Use for: daily delta loads simulating source system changes.

---

## Watermarks

Table: `audit.pipeline_watermarks`

| Column | Purpose |
|--------|---------|
| `pipeline_name` | e.g. `raw_ingestion` |
| `table_name` | e.g. `rides` |
| `watermark_ts` | High-water mark for incremental filter |
| `batch_id` | Last batch that updated watermark |
| `updated_at` | Audit timestamp |

Composite primary key: `(pipeline_name, table_name)`.

Watermarks are updated only when rows are actually loaded (`n > 0`).

---

## Idempotency

Running the same pipeline twice must **not duplicate** records.

### Mechanisms

| Layer | Strategy |
|-------|----------|
| **CSV dedupe** | `drop_duplicates(subset=natural_key, keep='last')` |
| **Full load** | Truncate before append |
| **Incremental** | Delete-by-key then append (upsert semantics) |
| **Natural keys** | Defined per table in `NATURAL_KEYS` dict |
| **Batch tracking** | Unique `batch_id` per run; logged in `audit.pipeline_runs` |
| **Anomaly table** | Truncate + reload each run |
| **dbt warehouse** | Table materialization replaces contents |

### Natural Keys

```text
cities       → city_id
zones        → zone_id
users        → user_id
drivers      → driver_id
vehicles     → vehicle_id
rides        → ride_id
driver_sessions → session_id
payments     → payment_id
ratings      → rating_id
promotions   → promotion_id
```

### Tests

`tests/test_idempotency.py` verifies duplicate handling and incremental behavior.

---

## Audit Logging

`audit.pipeline_runs` tracks each ingestion run:

| Field | Description |
|-------|-------------|
| run_id | UUID |
| pipeline_name | `raw_ingestion` or Airflow DAG name |
| start_time / end_time | Run duration |
| status | Running / Success / Failure |
| records_processed | Row count |
| records_failed | Error count |
| error_message | Failure detail |
| batch_id | Correlation ID |

---

## Airflow Orchestration

DAG: `airflow/dags/rideflow_daily_pipeline.py`

- Schedule: `@daily`
- `max_active_runs: 1` prevents overlapping batches
- Retries: 2 × 3 minutes
- Idempotent by design (same load_raw + dbt logic)

Start Airflow stack:

```bash
docker compose up -d
```

Trigger manually or wait for schedule. Web UI: `http://localhost:8080`.

---

## dbt Build Order

```text
staging.* (views)
  → intermediate.int_ride_fare_components
  → warehouse.* (dimensions before facts where referenced)
  → analytics.* (marts)
```

Command: `cd dbt && dbt build --profiles-dir .`

Runs models + tests. Failures in Airflow `data_quality_tests` task are tolerated (`|| true`) for resilience during development.

---

## Configuration

Environment variables (`.env`):

| Variable | Pipeline impact |
|----------|-----------------|
| `POSTGRES_*` | Connection |
| `NUM_*` | Generation volume |
| `BATCH_SIZE` | pandas `to_sql` chunk size |
| `FARE_TOLERANCE` | DQ fare check |
| `ANOMALY_ZSCORE_THRESHOLD` | Anomaly screening |

---

## Failure Handling

1. Ingestion exceptions → `pipeline_runs.status = 'Failure'`, error logged, exception re-raised
2. Validation failures → recorded in `dq_results.json`; pipeline may still proceed (review warnings)
3. Reconciliation FAIL → stored in `audit.reconciliation_results`; investigate before BI publish
4. Airflow retries transient task failures automatically

---

## Data Flow Diagram

```text
data/source/*.csv
       │
       ▼
[validate] ──► data/processed/dq_results.json
       │
       ▼
[load_raw full|incremental]
       │
       ▼
raw.* (+ batch_id, watermarks)
       │
       ▼
dbt: staging → warehouse → analytics
       │
       ├──► reconcile → audit.reconciliation_results
       └──► anomaly → monitoring.ride_anomalies
```
