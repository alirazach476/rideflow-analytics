# RideFlow KPI Definitions

All monetary values are in **RFU (RideFlow Units)** — fictional currency. Metrics are computed from `warehouse.fact_rides`, `warehouse.fact_payments`, and analytics marts unless noted.

---

## Core Ride KPIs

| KPI | Formula | SQL Pattern |
|-----|---------|-------------|
| **Total Rides** | Count of all ride events | `COUNT(*)` from `fact_rides` |
| **Completed Rides** | Rides with status Completed | `COUNT(*) FILTER (WHERE is_completed)` |
| **Cancelled Rides** | Rider or driver cancelled | `COUNT(*) FILTER (WHERE is_cancelled)` |
| **Completion Rate** | Completed ÷ Total | `100.0 * completed / NULLIF(total, 0)` |
| **Cancellation Rate** | Cancelled ÷ Total | `100.0 * cancelled / NULLIF(total, 0)` |
| **Total Revenue** | Sum of fares on completed rides | `SUM(total_fare) FILTER (WHERE is_completed)` |
| **Average Fare** | Mean fare (completed) | `AVG(total_fare) FILTER (WHERE is_completed)` |
| **Average Distance** | Mean km (completed) | `AVG(distance_km) FILTER (WHERE is_completed)` |
| **Average Duration** | Mean minutes (completed) | `AVG(duration_minutes) FILTER (WHERE is_completed)` |
| **Avg Fare per KM** | Revenue ÷ total distance | `SUM(total_fare) / NULLIF(SUM(distance_km), 0)` |
| **Avg Fare per Minute** | Revenue ÷ total duration | `SUM(total_fare) / NULLIF(SUM(duration_minutes), 0)` |

---

## Revenue Analytics

| KPI | Formula |
|-----|---------|
| **Gross Booking Value (GBV)** | `SUM(total_fare)` completed rides (before net adjustments) |
| **Net Revenue** | GBV − refunds − discounts (use payments mart for refunds) |
| **Average Revenue per Ride** | `Total Revenue / Completed Rides` |
| **Revenue per Driver** | `Total Revenue / DISTINCT active drivers` |
| **Revenue per User** | `Total Revenue / DISTINCT active users` |
| **Revenue by City** | `SUM(total_fare) GROUP BY city` |
| **Revenue by Vehicle Type** | Join `dim_vehicle`, aggregate |
| **Revenue by Payment Method** | From `fact_payments` |
| **MoM Revenue Growth** | `(Rev_current − Rev_prev) / Rev_prev` via `LAG()` |
| **YoY Revenue Growth** | Same formula, 12-month lag |

---

## Customer Metrics

| KPI | Formula |
|-----|---------|
| **Active Users** | Distinct `user_id` with completed ride in period |
| **New Users** | Users whose `registration_date` falls in period |
| **Repeat Users** | Users with ≥2 completed rides (lifetime or period) |
| **One-Time Users** | Users with exactly 1 completed ride |
| **Total Spend (per user)** | `SUM(total_fare)` per user, completed only |
| **Days Since Last Ride** | `CURRENT_DATE − MAX(request_timestamp::date)` |
| **30/60/90-Day Retention** | Cohort users with ride in window after signup |

### Customer Segments (rule-based)

| Segment | Rule |
|---------|------|
| Inactive | No ride in last 90 days |
| Low Activity | 1–5 completed rides lifetime |
| Medium Activity | 6–20 completed rides |
| High Activity | 21+ completed rides |
| Premium | `user_type = 'Premium'` OR avg fare > P75 |

---

## Driver Metrics

| KPI | Formula |
|-----|---------|
| **Active Drivers** | Distinct drivers with completed ride in period |
| **Acceptance Rate** | Accepted or completed ÷ (requested − no driver) |
| **Driver Cancellation Rate** | Driver cancelled ÷ total assigned |
| **Average Rating** | `AVG(rating)` from drivers or fact_ratings |
| **Revenue Generated** | `SUM(total_fare)` by driver |
| **Online Hours** | `SUM(online_minutes) / 60` from driver_sessions |
| **Rides per Online Hour** | `completed_rides / online_hours` |
| **Revenue per Online Hour** | `revenue / online_hours` |
| **Utilization Rate** | `completed_ride_minutes / online_minutes` (when available) |

---

## Supply vs Demand

| KPI | Formula |
|-----|---------|
| **Ride Requests** | Count rides by hour/city |
| **Active Drivers (supply)** | Distinct drivers in sessions or rides |
| **Driver Online Hours** | Sum from `fact_driver_sessions` |
| **Demand/Supply Ratio** | `ride_requests / NULLIF(available_drivers, 0)` |

### Pressure Classification (documented thresholds)

| Level | Ratio |
|-------|-------|
| Low Demand | < 0.5 |
| Balanced | 0.5 – 1.5 |
| High Demand | 1.5 – 3.0 |
| Severe Pressure | > 3.0 |

---

## Surge Metrics

| KPI | Formula |
|-----|---------|
| **Average Surge Multiplier** | `AVG(surge_multiplier)` completed rides |
| **Surge Revenue** | `SUM(total_fare)` where surge > 1.0 |
| **Completion Rate by Surge** | Completion rate grouped by surge bucket |
| **Cancellation Rate by Surge** | Cancellation rate grouped by surge bucket |

---

## Cancellation Metrics

| KPI | Formula |
|-----|---------|
| **Rider Cancellation Rate** | Rider cancelled ÷ total |
| **Driver Cancellation Rate** | Driver cancelled ÷ total |
| **Cancel Rate by City/Hour/Vehicle** | Grouped cancellation rate |

---

## Payment Metrics

| KPI | Formula |
|-----|---------|
| **Payment Count** | `COUNT(*)` from fact_payments |
| **Payment Value** | `SUM(amount)` |
| **Success Rate** | Completed payments ÷ all payments |
| **Failure Rate** | Failed ÷ all |
| **Refund Amount** | `SUM(amount)` where status = Refunded |
| **Method Share** | `COUNT(*) / SUM(COUNT(*)) OVER ()` by method |

---

## Rating Metrics

| KPI | Formula |
|-----|---------|
| **Average Driver Rating** | Mean rating to drivers |
| **Rating Distribution** | Count by rating 1–5 |
| **Drivers Below 4.5** | Count where avg rating < 4.5 |
| **Drivers Above 4.8** | Count where avg rating > 4.8 |

---

## Anomaly Metrics (Screening)

| KPI | Formula |
|-----|---------|
| **Anomaly Count** | Rows in `monitoring.ride_anomalies` |
| **Anomaly Rate** | Anomalies ÷ completed rides |
| **High-Severity Count** | Where severity IN ('High', 'Critical') |

> Anomaly rate measures **screening volume**, not confirmed fraud.

---

## Power BI DAX Equivalents

See `dashboards/powerbi/dax_measures.md` for DAX implementations of core KPIs.
