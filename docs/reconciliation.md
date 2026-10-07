# RideFlow Data Reconciliation

Reconciliation verifies that key business metrics **agree across pipeline layers** after transformation. Results are persisted — never fabricated.

---

## Purpose

After dbt builds the warehouse, RideFlow compares aggregate metrics between:

| Layer | Role |
|-------|------|
| **raw** | Post-ingestion landing (source of truth for counts) |
| **warehouse** | Transformed star schema |

Future extension: compare `warehouse` → `analytics` marts for mart-level QA.

---

## Implementation

| Item | Location |
|------|----------|
| Python runner | `src/transformation/reconcile.py` |
| SQL reference | `sql/reconciliation/reconcile_metrics.sql` |
| Command | `make reconcile` |
| Storage | `audit.reconciliation_results` |

Each run generates a unique `run_id` (UUID).

---

## Metrics Compared

| Metric | Source (raw) | Warehouse |
|--------|--------------|-----------|
| **ride_count** | `COUNT(DISTINCT ride_id) FROM raw.rides` | `COUNT(*) FROM warehouse.fact_rides` |
| **completed_ride_count** | Completed in raw | `is_completed = TRUE` in fact_rides |
| **revenue** | `SUM(total_fare)` completed raw rides | Same on fact_rides |
| **payment_amount** | `SUM(amount)` completed payments | `SUM(amount)` on fact_payments |

---

## Status Logic

For each metric, compute:

```text
difference = warehouse_value − source_value
pct_diff   = |difference| / |source_value|   (or 1 if source = 0)
```

| Status | Condition |
|--------|-----------|
| **PASS** | pct_diff ≤ 1% |
| **WARNING** | 1% < pct_diff ≤ 5% |
| **FAIL** | pct_diff > 5% |

If warehouse table is missing (dbt not run), status defaults to **WARNING**.

---

## Result Schema

`audit.reconciliation_results`:

| Column | Description |
|--------|-------------|
| reconciliation_id | Serial PK |
| run_id | Batch correlation |
| metric_name | e.g. `revenue` |
| source_value | Raw-layer aggregate |
| warehouse_value | Warehouse aggregate |
| difference | Numeric delta |
| status | PASS / WARNING / FAIL |
| checked_at | Timestamp |

---

## Example Query

```sql
SELECT metric_name, source_value, warehouse_value, difference, status, checked_at
FROM audit.reconciliation_results
ORDER BY checked_at DESC, reconciliation_id DESC
LIMIT 20;
```

---

## When Discrepancies Occur

| Cause | Typical impact |
|-------|----------------|
| dbt not run | WARNING (warehouse empty) |
| Staging filters dropped bad rides | ride_count mismatch |
| Status normalization | completed count slight diff |
| Duplicate source rows pre-dedupe | Should be resolved by ingest dedupe |
| Payment status casing | payment_amount diff |

**Action:** Investigate staging models and ingest dedupe logs before publishing dashboards.

---

## Pipeline Integration

Reconciliation runs:
- After `make dbt-build` in `make pipeline`
- As Airflow task `reconciliation` (post `dbt_analytics`)
- On demand via `make reconcile`

---

## Idempotency Note

Each reconciliation run **appends** new rows to `audit.reconciliation_results`. Historical runs support trend analysis of metric drift over time.

---

## Limitations

- Does not yet reconcile analytics marts row-by-row
- Does not compare CSV file counts directly (uses raw post-ingest)
- Tolerance thresholds are percentage-based, not absolute RFU for revenue

These are acceptable for a local demo platform; production would add mart-level and partition-level checks.
