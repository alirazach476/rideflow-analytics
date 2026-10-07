# RideFlow Power BI Dashboard Specification

Connect Power BI Desktop to PostgreSQL (`analytics` + `warehouse` schemas).

**Label for anomaly page:** Analytical anomaly monitoring — not fraud confirmation.

## Data Model Relationships

| From | To | Key | Cardinality |
|------|-----|-----|-------------|
| fact_rides | dim_date | date_key | Many:1 |
| fact_rides | dim_time | time_key | Many:1 |
| fact_rides | dim_user | user_key | Many:1 |
| fact_rides | dim_driver | driver_key | Many:1 |
| fact_rides | dim_vehicle | vehicle_key | Many:1 |
| fact_rides | dim_city | city_key | Many:1 |
| fact_rides | dim_zone (pickup) | pickup_zone_key | Many:1 |
| fact_rides | dim_zone (dropoff) | dropoff_zone_key | Many:1 |
| fact_rides | dim_ride_status | status_key | Many:1 |
| fact_payments | dim_payment_method | payment_method_key | Many:1 |

Use star schema; hide surrogate keys from report view.

## Pages

### Page 1 — Executive Overview
KPIs: Total Rides, Completed Rides, Completion Rate, Total Revenue, Average Fare, Active Users, Active Drivers, Cancellation Rate  
Charts: revenue trend, ride trend, revenue by city, rides by vehicle type, status distribution, hourly demand, supply vs demand  
Slicers: Date, City, Vehicle Type, User Type, Payment Method

### Page 2 — Ride Analytics
Daily/monthly rides, completed vs cancelled, avg fare/distance/duration, status, vehicle, payment, hourly volume

### Page 3 — Customer Analytics
Active/new/repeat/one-time users, segments, revenue, rides per user, retention, cohort heatmap (`mart_cohort_retention`)

### Page 4 — Driver Analytics
Active drivers, completed rides, rating, utilization, revenue/driver, rides/online hour, top drivers, cancel rate

### Page 5 — City & Zone Analytics
Revenue/volume by city, demand/supply by zone, top pickup/dropoff, cancellation hotspots

### Page 6 — Surge & Pricing
Avg surge, revenue vs surge, demand vs surge, cancel/completion vs surge, fare distribution, fare by vehicle

### Page 7 — Cancellation Analytics
Rider/driver cancel rates by city/hour/vehicle/surge/reason (`mart_cancellation_analysis`)

### Page 8 — Anomaly Monitoring
Potential anomalies, severity, reasons, city, time — clearly labeled as analytical screening only

### Page 9 — Data Quality
PASS/WARNING/FAIL from `audit.data_quality_results` and `audit.reconciliation_results`

## Primary Tables for Import

- `analytics.mart_daily_ride_metrics`
- `analytics.mart_city_performance`
- `analytics.mart_zone_performance`
- `analytics.mart_user_activity`
- `analytics.mart_driver_performance`
- `analytics.mart_surge_analysis`
- `analytics.mart_supply_demand`
- `analytics.mart_cancellation_analysis`
- `analytics.mart_payment_performance`
- `monitoring.ride_anomalies`
- `warehouse.fact_rides` (if detail needed)
- `warehouse.dim_*`
