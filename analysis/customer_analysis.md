# RideFlow Customer Analysis

Structured analysis template for customer analytics. **Results populated after pipeline run.**

---

## Methodology

### Data Sources

| Table / Mart | Purpose |
|--------------|---------|
| `warehouse.fact_rides` | Ride events per user |
| `warehouse.dim_user` | Segments (filter `is_current = TRUE`) |
| `analytics.mart_user_activity` | Pre-aggregated user metrics |
| `analytics.mart_cohort_retention` | Retention cohorts |

### Metrics Computed

| Metric | Definition |
|--------|------------|
| total_rides | All ride requests by user |
| completed_rides | Completed only |
| cancelled_rides | Rider + driver cancelled |
| total_spend | SUM(total_fare) completed |
| average_fare | Mean fare completed |
| average_distance | Mean km completed |
| last_ride_date | MAX(request_timestamp) |
| days_since_last_ride | Current date − last ride |

### Segmentation Rules

| Segment | Criteria |
|---------|----------|
| Inactive | No completed ride in 90 days |
| Low Activity | 1–5 completed rides |
| Medium Activity | 6–20 completed rides |
| High Activity | 21+ completed rides |
| Premium | user_type = Premium OR avg fare > P75 |

---

## Analysis Questions

1. How many active vs inactive users?
2. What is average rides per user by segment?
3. Which signup channel produces highest-LTV users?
4. What is 30/60/90-day cohort retention?
5. How does Premium segment compare on spend and frequency?

---

## SQL Starting Points

```sql
-- User segment summary (run after pipeline)
SELECT user_type, COUNT(*) AS users
FROM warehouse.dim_user
WHERE is_current = TRUE
GROUP BY user_type
ORDER BY users DESC;
```

```sql
-- Top spenders (completed rides)
SELECT user_id, SUM(total_fare) AS total_spend, COUNT(*) AS rides
FROM warehouse.fact_rides
WHERE is_completed = TRUE
GROUP BY user_id
ORDER BY total_spend DESC
LIMIT 20;
```

See also: `sql/analytics/03_customer_driver.sql`

---

## Results

> **Status:** _Pending — run `make pipeline` then query marts._

| Metric | Value |
|--------|-------|
| Total users | _TBD_ |
| Active users (period) | _TBD_ |
| Repeat user rate | _TBD_ |
| Avg rides per active user | _TBD_ |
| Top segment by revenue | _TBD_ |
| 30-day retention | _TBD_ |

---

## Observations

_To be filled from SQL results._

---

## Limitations

- Synthetic behavior may not match real market dynamics
- SCD Type 2 user history limited on initial load
- Segments are rule-based, not ML-derived clusters
