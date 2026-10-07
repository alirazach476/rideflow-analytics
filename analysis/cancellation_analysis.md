# RideFlow Cancellation Analysis

Structured template for cancellation analytics. **Results populated after pipeline run.**

---

## Methodology

### Data Sources

| Table / Mart | Purpose |
|--------------|---------|
| `warehouse.fact_rides` | Status, reasons, cancelled_by |
| `analytics.mart_cancellation_analysis` | Multi-dimensional cancel metrics |
| `warehouse.dim_city`, `dim_zone`, `dim_vehicle` | Breakdown dimensions |

### Ride Statuses (Cancelled)

| Status | Actor |
|--------|-------|
| Rider_Cancelled | Passenger |
| Driver_Cancelled | Driver |

### Documented Reason Categories

**Rider:** Long ETA, High Fare, Driver Delayed, Changed Mind, Other  
**Driver:** Too Far, Low Fare, Traffic, Vehicle Issue, Personal Reason, Other

### Metrics

| Metric | Formula |
|--------|---------|
| rider_cancel_rate | Rider cancelled / total rides |
| driver_cancel_rate | Driver cancelled / total rides |
| overall_cancel_rate | All cancelled / total |
| cancel_rate_by_dimension | GROUP BY city, hour, vehicle, surge bucket |

---

## Analysis Questions

1. Is cancellation higher during surge periods?
2. Which city has the worst rider cancel rate?
3. Which hours see most driver cancellations?
4. Do certain vehicle types correlate with higher cancels?
5. What are the top stated cancellation reasons?

---

## SQL Starting Points

```sql
-- Overall cancellation breakdown
SELECT
    ride_status,
    COUNT(*) AS rides,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM warehouse.fact_rides
WHERE is_cancelled = TRUE OR ride_status IN ('Rider_Cancelled', 'Driver_Cancelled')
GROUP BY ride_status;
```

```sql
-- Cancellation by city
SELECT c.city_name,
       COUNT(*) FILTER (WHERE f.ride_status = 'Rider_Cancelled') AS rider_cancels,
       COUNT(*) FILTER (WHERE f.ride_status = 'Driver_Cancelled') AS driver_cancels,
       COUNT(*) AS total_rides
FROM warehouse.fact_rides f
JOIN warehouse.dim_city c ON f.city_key = c.city_key
GROUP BY c.city_name
ORDER BY rider_cancels + driver_cancels DESC;
```

See also: `sql/analytics/04_geo_surge_cancel.sql`

---

## Results

> **Status:** _Pending — run `make pipeline` then query marts._

| Metric | Value |
|--------|-------|
| Overall cancellation rate | _TBD_ |
| Rider cancel rate | _TBD_ |
| Driver cancel rate | _TBD_ |
| Highest cancel city | _TBD_ |
| Peak cancel hour | _TBD_ |
| Top rider reason | _TBD_ |
| Top driver reason | _TBD_ |
| Cancel rate at surge ≥ 1.5 | _TBD_ |

---

## Hypotheses to Test (data-driven)

| Hypothesis | Test |
|------------|------|
| High surge → more rider cancels | Compare cancel rate by surge bucket |
| Airport zones → longer ETA cancels | Zone-level rider cancel rate |
| Low-rated drivers → more cancels | Join driver rating to cancel rate |

_Do not assume outcomes — measure from SQL._

---

## Observations

_To be filled from SQL results._

---

## Limitations

- Cancellation reasons are synthetic/simplified
- No post-cancel survey or NLP on free text
- Correlation ≠ causation for surge and cancel patterns
