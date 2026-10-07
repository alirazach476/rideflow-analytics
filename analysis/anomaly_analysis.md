# RideFlow Anomaly Analysis

Structured template for **analytical anomaly screening** review. **Results populated after pipeline run.**

> **Disclaimer:** Flagged rides are *potential anomalies requiring review* — **NOT confirmed fraud**.

---

## Methodology

### Data Sources

| Table | Purpose |
|-------|---------|
| `monitoring.ride_anomalies` | Flagged rides with reasons and severity |
| `analytics.mart_anomaly_monitoring` | Summary aggregates |
| `warehouse.fact_rides` | Context for flagged rides |

### Detection Methods

1. **Rule-based** — fare/distance/duration extremes, rapid repeat rides, late-night high value
2. **Z-score** — customer fare deviation (threshold: `ANOMALY_ZSCORE_THRESHOLD`)
3. **Isolation Forest** (optional) — multivariate pattern screening

### Severity Levels

Low → Medium → High → Critical (by composite rule score)

---

## Analysis Questions

1. How many rides were flagged vs total completed?
2. What is the severity distribution?
3. Which cities have the most flags?
4. What are the most common anomaly reasons?
5. Do flagged rides cluster in time (hour/day)?
6. Which users appear repeatedly in flags? (review list, not accusation)

---

## SQL Starting Points

```sql
-- Anomaly summary
SELECT severity, COUNT(*) AS flag_count
FROM monitoring.ride_anomalies
GROUP BY severity
ORDER BY flag_count DESC;
```

```sql
-- Top reasons
SELECT anomaly_reason, COUNT(*) AS cnt
FROM monitoring.ride_anomalies
GROUP BY anomaly_reason
ORDER BY cnt DESC
LIMIT 10;
```

```sql
-- Anomaly rate
SELECT
    (SELECT COUNT(*) FROM monitoring.ride_anomalies) AS anomalies,
    (SELECT COUNT(*) FROM warehouse.fact_rides WHERE is_completed) AS completed,
    ROUND(100.0 * (SELECT COUNT(*) FROM monitoring.ride_anomalies)
          / NULLIF((SELECT COUNT(*) FROM warehouse.fact_rides WHERE is_completed), 0), 4) AS anomaly_rate_pct;
```

Run detection: `make anomaly-detection`

---

## Results

> **Status:** _Pending — run `make pipeline` then `make anomaly-detection`._

| Metric | Value |
|--------|-------|
| Completed rides scanned | _TBD_ |
| Total anomalies flagged | _TBD_ |
| Anomaly rate (%) | _TBD_ |
| Critical severity count | _TBD_ |
| High severity count | _TBD_ |
| Top anomaly reason | _TBD_ |
| Top city by flags | _TBD_ |

---

## Review Workflow (Recommended)

```text
1. Filter Critical / High severity in Power BI Page 8
2. Read anomaly_reason for business context
3. Pull ride detail from fact_rides (distance, duration, user history)
4. Mark as: Valid edge case | Data quality issue | Needs investigation
5. Do NOT auto-block user/driver based on flag alone
```

---

## Expected False Positives

| Pattern | Why flagged | Likely valid? |
|---------|-------------|---------------|
| Long airport ride | High distance/duration | Often yes |
| Premium user high fare | Z-score | Often yes |
| Multiple short trips | Rapid repeat rule | Context-dependent |

---

## Observations

_To be filled from SQL results._

---

## Limitations

- Batch screening only — not real-time
- No network/graph analysis
- Isolation Forest not explainable per-feature in output
- Not a substitute for fraud ops, legal, or payment dispute processes
- pandas-based — scale limits on very large datasets
