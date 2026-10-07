-- Advanced SQL patterns: CTE, subquery, percentiles, conditional aggregation

-- Q25: Percentile fares by city
SELECT
    c.city_name,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.total_fare)::NUMERIC, 2) AS p50_fare,
    ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY f.total_fare)::NUMERIC, 2) AS p90_fare,
    ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY f.total_fare)::NUMERIC, 2) AS p99_fare
FROM warehouse.fact_rides f
JOIN warehouse.dim_city c ON f.city_key = c.city_key
WHERE f.is_completed AND f.total_fare IS NOT NULL
GROUP BY c.city_name
ORDER BY p50_fare DESC;

-- Q26: Weekend vs weekday behavior
SELECT
    CASE WHEN d.is_weekend THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    COUNT(*) AS rides,
    ROUND(AVG(f.total_fare) FILTER (WHERE f.is_completed)::NUMERIC, 2) AS avg_fare,
    ROUND(100.0 * COUNT(*) FILTER (WHERE f.is_cancelled) / NULLIF(COUNT(*), 0), 2) AS cancel_rate
FROM warehouse.fact_rides f
JOIN warehouse.dim_date d ON f.date_key = d.date_key
GROUP BY 1;

-- Q27: Peak commute periods
SELECT
    t.peak_period,
    COUNT(*) AS rides,
    ROUND(SUM(f.total_fare) FILTER (WHERE f.is_completed)::NUMERIC, 2) AS revenue
FROM warehouse.fact_rides f
JOIN warehouse.dim_time t ON f.time_key = t.time_key
GROUP BY t.peak_period
ORDER BY rides DESC;

-- Q28: Users with spend above city average (subquery)
SELECT
    u.user_id,
    u.total_spend,
    u.customer_segment
FROM analytics.mart_user_activity u
WHERE u.total_spend > (
    SELECT AVG(total_spend) FROM analytics.mart_user_activity WHERE total_spend > 0
)
ORDER BY u.total_spend DESC
LIMIT 50;

-- Q29: Revenue by day of week
SELECT
    d.day_name,
    ROUND(SUM(f.total_fare) FILTER (WHERE f.is_completed)::NUMERIC, 2) AS revenue,
    COUNT(*) AS rides
FROM warehouse.fact_rides f
JOIN warehouse.dim_date d ON f.date_key = d.date_key
GROUP BY d.day_name, d.day
ORDER BY d.day;

-- Q30: YoY revenue growth (when date range supports it)
WITH yearly AS (
    SELECT d.year, SUM(f.total_fare) FILTER (WHERE f.is_completed) AS revenue
    FROM warehouse.fact_rides f
    JOIN warehouse.dim_date d ON f.date_key = d.date_key
    GROUP BY d.year
)
SELECT
    year,
    ROUND(revenue::NUMERIC, 2) AS revenue,
    ROUND(LAG(revenue) OVER (ORDER BY year)::NUMERIC, 2) AS prev_year,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year))
          / NULLIF(LAG(revenue) OVER (ORDER BY year), 0), 2) AS yoy_growth_pct
FROM yearly
ORDER BY year;

-- Q31: Dropoff hotspots
SELECT
    z.zone_name,
    COUNT(*) AS dropoff_volume,
    ROUND(SUM(f.total_fare) FILTER (WHERE f.is_completed)::NUMERIC, 2) AS revenue
FROM warehouse.fact_rides f
JOIN warehouse.dim_zone z ON f.dropoff_zone_key = z.zone_key
GROUP BY z.zone_name
ORDER BY dropoff_volume DESC
LIMIT 15;

-- Q32: Payment success by method with CASE
SELECT
    payment_method,
    SUM(CASE WHEN payment_status = 'Completed' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN payment_status = 'Failed' THEN 1 ELSE 0 END) AS failed,
    SUM(CASE WHEN payment_status = 'Refunded' THEN 1 ELSE 0 END) AS refunded,
    ROUND(AVG(amount)::NUMERIC, 2) AS avg_amount
FROM warehouse.fact_payments
GROUP BY payment_method;

-- Q33: Rating distribution
SELECT rating, COUNT(*) AS n, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM warehouse.fact_ratings
GROUP BY rating
ORDER BY rating DESC;

-- Q34: Active users and drivers (trailing window conceptually via DISTINCT)
SELECT
    COUNT(DISTINCT CASE WHEN is_completed THEN user_id END) AS active_users,
    COUNT(DISTINCT CASE WHEN is_completed THEN driver_id END) AS active_drivers
FROM warehouse.fact_rides;

-- Q35: Cities with cancellation rate above overall average (HAVING + subquery)
SELECT
    city_name,
    cancellation_rate,
    total_revenue
FROM analytics.mart_city_performance
WHERE cancellation_rate > (
    SELECT AVG(cancellation_rate) FROM analytics.mart_city_performance
)
ORDER BY cancellation_rate DESC;
