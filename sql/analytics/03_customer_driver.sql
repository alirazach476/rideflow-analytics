-- Customer & driver analytics

-- Q11: Customer segments summary
SELECT customer_segment, COUNT(*) AS users, ROUND(SUM(total_spend)::NUMERIC, 2) AS spend
FROM analytics.mart_user_activity
GROUP BY customer_segment
ORDER BY spend DESC NULLS LAST;

-- Q12: New vs repeat vs one-time users (CTE)
WITH completed AS (
    SELECT user_id, COUNT(*) AS completed_rides
    FROM warehouse.fact_rides
    WHERE is_completed
    GROUP BY user_id
)
SELECT
    COUNT(*) FILTER (WHERE completed_rides = 1) AS one_time_users,
    COUNT(*) FILTER (WHERE completed_rides > 1) AS repeat_users,
    COUNT(*) AS users_with_completed_rides
FROM completed;

-- Q13: 30/60/90 day retention proxy
SELECT
    signup_month,
    cohort_users,
    retained_30d,
    retained_60d,
    retained_90d,
    ROUND(100.0 * retained_30d / NULLIF(cohort_users, 0), 2) AS retention_30d_pct
FROM analytics.mart_cohort_retention
WHERE signup_month IS NOT NULL
ORDER BY signup_month
LIMIT 24;

-- Q14: Top drivers by revenue per online hour
SELECT
    driver_id,
    driver_type,
    completed_rides,
    online_hours,
    revenue_per_online_hour,
    rides_per_online_hour,
    revenue_rank
FROM analytics.mart_driver_performance
WHERE online_hours > 0
ORDER BY revenue_per_online_hour DESC NULLS LAST
LIMIT 20;

-- Q15: Drivers below 4.5 and above 4.8
SELECT
    CASE
        WHEN average_rating < 4.5 THEN 'Below 4.5'
        WHEN average_rating > 4.8 THEN 'Above 4.8'
        ELSE '4.5–4.8'
    END AS rating_band,
    COUNT(*) AS drivers
FROM analytics.mart_driver_performance
WHERE average_rating IS NOT NULL
GROUP BY 1;

-- Q16: Acceptance / cancellation by driver type
SELECT
    driver_type,
    ROUND(AVG(cancellation_rate)::NUMERIC, 2) AS avg_cancel_rate,
    ROUND(AVG(average_rating)::NUMERIC, 2) AS avg_rating,
    ROUND(SUM(revenue_generated)::NUMERIC, 2) AS total_revenue
FROM analytics.mart_driver_performance
GROUP BY driver_type;
