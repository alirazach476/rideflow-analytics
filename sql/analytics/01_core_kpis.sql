-- RideFlow Advanced SQL Analytics
-- 01 Core Ride KPIs

-- Q01: Overall ride KPIs
SELECT
    COUNT(*) AS total_rides,
    COUNT(*) FILTER (WHERE is_completed) AS completed_rides,
    COUNT(*) FILTER (WHERE is_cancelled) AS cancelled_rides,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_completed) / NULLIF(COUNT(*), 0), 2) AS completion_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_cancelled) / NULLIF(COUNT(*), 0), 2) AS cancellation_rate,
    ROUND(SUM(total_fare) FILTER (WHERE is_completed)::NUMERIC, 2) AS total_revenue,
    ROUND(AVG(total_fare) FILTER (WHERE is_completed)::NUMERIC, 2) AS average_fare,
    ROUND(AVG(distance_km) FILTER (WHERE is_completed)::NUMERIC, 2) AS average_distance,
    ROUND(AVG(duration_minutes) FILTER (WHERE is_completed)::NUMERIC, 2) AS average_duration,
    ROUND((SUM(total_fare) FILTER (WHERE is_completed)
           / NULLIF(SUM(distance_km) FILTER (WHERE is_completed), 0))::NUMERIC, 2) AS avg_fare_per_km,
    ROUND((SUM(total_fare) FILTER (WHERE is_completed)
           / NULLIF(SUM(duration_minutes) FILTER (WHERE is_completed), 0))::NUMERIC, 2) AS avg_fare_per_minute
FROM warehouse.fact_rides;

-- Q02: Revenue by city (JOIN + GROUP BY)
SELECT
    c.city_name,
    COUNT(*) FILTER (WHERE f.is_completed) AS completed_rides,
    ROUND(SUM(f.total_fare) FILTER (WHERE f.is_completed)::NUMERIC, 2) AS revenue
FROM warehouse.fact_rides f
INNER JOIN warehouse.dim_city c ON f.city_key = c.city_key
GROUP BY c.city_name
ORDER BY revenue DESC NULLS LAST;

-- Q03: Rides by vehicle type
SELECT
    v.vehicle_type,
    COUNT(*) AS rides,
    ROUND(AVG(f.total_fare) FILTER (WHERE f.is_completed)::NUMERIC, 2) AS avg_fare
FROM warehouse.fact_rides f
LEFT JOIN warehouse.dim_vehicle v ON f.vehicle_key = v.vehicle_key
GROUP BY v.vehicle_type
ORDER BY rides DESC;

-- Q04: Payment method share
SELECT
    payment_method,
    COUNT(*) AS payments,
    ROUND(SUM(amount)::NUMERIC, 2) AS value,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS share_pct
FROM warehouse.fact_payments
GROUP BY payment_method
ORDER BY payments DESC;

-- Q05: Busiest hours
SELECT
    EXTRACT(HOUR FROM request_timestamp)::INT AS hour_of_day,
    COUNT(*) AS ride_requests,
    COUNT(*) FILTER (WHERE is_completed) AS completed
FROM warehouse.fact_rides
GROUP BY 1
ORDER BY ride_requests DESC;
