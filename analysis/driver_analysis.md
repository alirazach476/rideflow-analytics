# RideFlow Driver Analysis

Structured analysis template for driver/supply analytics. **Results populated after pipeline run.**

---

## Methodology

### Data Sources

| Table / Mart | Purpose |
|--------------|---------|
| `warehouse.fact_rides` | Completed/cancelled rides by driver |
| `warehouse.fact_driver_sessions` | Online time and supply |
| `warehouse.dim_driver` | Driver attributes, rating |
| `analytics.mart_driver_performance` | Aggregated KPIs |
| `analytics.mart_supply_demand` | Hourly supply metrics |

### Metrics Computed

| Metric | Formula |
|--------|---------|
| completed_rides | COUNT completed by driver |
| acceptance_rate | Accepted+completed / assignable requests |
| driver_cancel_rate | Driver cancelled / total assigned |
| revenue_generated | SUM(total_fare) completed |
| online_hours | SUM(online_minutes) / 60 |
| rides_per_online_hour | completed_rides / online_hours |
| revenue_per_online_hour | revenue / online_hours |
| average_rating | From dim_driver or fact_ratings |

### Ranking

Drivers ranked using `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()` over monthly revenue (see `sql/analytics/03_customer_driver.sql`).

---

## Analysis Questions

1. Who are the top 10 drivers by revenue?
2. How does utilization vary by city and hour?
3. Which driver types (Full-Time vs Part-Time) have best rides/online hour?
4. Is there correlation between rating and cancellation rate?
5. Where is supply insufficient relative to demand?

---

## SQL Starting Points

```sql
-- Top drivers by revenue
SELECT driver_id, COUNT(*) AS rides, ROUND(SUM(total_fare)::NUMERIC, 2) AS revenue
FROM warehouse.fact_rides
WHERE is_completed = TRUE AND driver_id IS NOT NULL
GROUP BY driver_id
ORDER BY revenue DESC
LIMIT 10;
```

```sql
-- Utilization from sessions
SELECT driver_id,
       SUM(online_minutes) / 60.0 AS online_hours,
       SUM(rides_completed) AS rides,
       ROUND(SUM(rides_completed) / NULLIF(SUM(online_minutes) / 60.0, 0), 2) AS rides_per_hour
FROM warehouse.fact_driver_sessions
GROUP BY driver_id
ORDER BY rides_per_hour DESC NULLS LAST
LIMIT 20;
```

---

## Results

> **Status:** _Pending — run `make pipeline` then query marts._

| Metric | Value |
|--------|-------|
| Total drivers | _TBD_ |
| Active drivers | _TBD_ |
| Avg driver rating | _TBD_ |
| Avg rides per online hour | _TBD_ |
| Top driver revenue (RFU) | _TBD_ |
| Highest utilization city | _TBD_ |

---

## Observations

_To be filled from SQL results._

---

## Limitations

- Session data may not perfectly align with ride timestamps
- Synthetic ratings clustered around 4.1–4.9
- No real GPS/track validation of driver behavior
