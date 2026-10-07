-- Geographic, surge, cancellation, supply-demand

-- Q17: Top pickup zones
SELECT zone_name, zone_type, pickup_volume, revenue, cancellation_rate
FROM analytics.mart_zone_performance
ORDER BY pickup_volume DESC
LIMIT 15;

-- Q18: Origin-destination popular routes
SELECT
    pz.zone_name AS pickup_zone,
    dz.zone_name AS dropoff_zone,
    COUNT(*) AS ride_count,
    ROUND(SUM(f.total_fare) FILTER (WHERE f.is_completed)::NUMERIC, 2) AS revenue,
    ROUND(AVG(f.distance_km) FILTER (WHERE f.is_completed)::NUMERIC, 2) AS avg_distance,
    ROUND(AVG(f.duration_minutes) FILTER (WHERE f.is_completed)::NUMERIC, 2) AS avg_duration,
    ROUND(AVG(f.total_fare) FILTER (WHERE f.is_completed)::NUMERIC, 2) AS avg_fare,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS popularity_rank
FROM warehouse.fact_rides f
JOIN warehouse.dim_zone pz ON f.pickup_zone_key = pz.zone_key
JOIN warehouse.dim_zone dz ON f.dropoff_zone_key = dz.zone_key
WHERE f.is_completed
GROUP BY 1,2
ORDER BY ride_count DESC
LIMIT 25;

-- Q19: Surge vs revenue / completion / cancellation
SELECT *
FROM analytics.mart_surge_analysis
ORDER BY surge_multiplier;

-- Q20: Correlation proxy — surge vs cancellation (city level)
SELECT
    CORR(average_surge, cancellation_rate) AS surge_cancel_corr,
    CORR(average_surge, total_revenue) AS surge_revenue_corr
FROM analytics.mart_city_performance;

-- Q21: Cancellation reasons
SELECT
    cancelled_by,
    cancellation_reason,
    SUM(cancellations) AS total
FROM analytics.mart_cancellation_analysis
GROUP BY 1,2
ORDER BY total DESC;

-- Q22: Cancellation by hour
SELECT
    hour_of_day,
    SUM(cancellations) AS cancellations
FROM analytics.mart_cancellation_analysis
GROUP BY 1
ORDER BY 1;

-- Q23: Supply-demand pressure bands
SELECT
    demand_pressure_band,
    COUNT(*) AS hour_buckets,
    ROUND(AVG(demand_supply_ratio)::NUMERIC, 3) AS avg_ratio
FROM analytics.mart_supply_demand
GROUP BY 1
ORDER BY avg_ratio DESC NULLS LAST;

-- Q24: High demand / low supply zones (HAVING)
SELECT
    city_id,
    hour_of_day,
    AVG(demand_supply_ratio) AS avg_ratio,
    SUM(ride_requests) AS requests
FROM analytics.mart_supply_demand
GROUP BY 1,2
HAVING AVG(demand_supply_ratio) >= 3.0
ORDER BY avg_ratio DESC
LIMIT 20;
