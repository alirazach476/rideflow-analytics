-- Window functions: ranking, running totals, rolling averages, LAG/LEAD

-- Q06: Driver ranking by monthly revenue (ROW_NUMBER, RANK, DENSE_RANK)
WITH monthly AS (
    SELECT
        f.driver_id,
        d.year,
        d.month,
        SUM(f.total_fare) FILTER (WHERE f.is_completed) AS revenue
    FROM warehouse.fact_rides f
    JOIN warehouse.dim_date d ON f.date_key = d.date_key
    WHERE f.driver_id IS NOT NULL
    GROUP BY 1,2,3
)
SELECT
    driver_id,
    year,
    month,
    ROUND(revenue::NUMERIC, 2) AS revenue,
    ROW_NUMBER() OVER (PARTITION BY year, month ORDER BY revenue DESC NULLS LAST) AS rn,
    RANK() OVER (PARTITION BY year, month ORDER BY revenue DESC NULLS LAST) AS rnk,
    DENSE_RANK() OVER (PARTITION BY year, month ORDER BY revenue DESC NULLS LAST) AS dense_rnk
FROM monthly
WHERE revenue IS NOT NULL
ORDER BY year, month, rn
LIMIT 100;

-- Q07: Cumulative monthly revenue (running total)
WITH monthly_rev AS (
    SELECT
        d.year,
        d.month,
        SUM(f.total_fare) FILTER (WHERE f.is_completed) AS revenue
    FROM warehouse.fact_rides f
    JOIN warehouse.dim_date d ON f.date_key = d.date_key
    GROUP BY 1,2
)
SELECT
    year,
    month,
    ROUND(revenue::NUMERIC, 2) AS revenue,
    ROUND(SUM(revenue) OVER (ORDER BY year, month)::NUMERIC, 2) AS cumulative_revenue
FROM monthly_rev
ORDER BY year, month;

-- Q08: 7-day rolling average of rides
WITH daily AS (
    SELECT
        d.full_date,
        COUNT(*) AS rides
    FROM warehouse.fact_rides f
    JOIN warehouse.dim_date d ON f.date_key = d.date_key
    GROUP BY d.full_date
)
SELECT
    full_date,
    rides,
    ROUND(AVG(rides) OVER (
        ORDER BY full_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    )::NUMERIC, 2) AS rides_7d_avg
FROM daily
ORDER BY full_date;

-- Q09: MoM revenue with LAG
WITH monthly_rev AS (
    SELECT
        d.year,
        d.month,
        SUM(f.total_fare) FILTER (WHERE f.is_completed) AS revenue
    FROM warehouse.fact_rides f
    JOIN warehouse.dim_date d ON f.date_key = d.date_key
    GROUP BY 1,2
)
SELECT
    year,
    month,
    ROUND(revenue::NUMERIC, 2) AS revenue,
    ROUND(LAG(revenue) OVER (ORDER BY year, month)::NUMERIC, 2) AS prev_month_revenue,
    ROUND(LEAD(revenue) OVER (ORDER BY year, month)::NUMERIC, 2) AS next_month_revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY year, month))
        / NULLIF(LAG(revenue) OVER (ORDER BY year, month), 0)
    , 2) AS mom_growth_pct
FROM monthly_rev
ORDER BY year, month;

-- Q10: User ride sequence with LEAD/LAG
SELECT
    user_id,
    ride_id,
    request_timestamp,
    LAG(request_timestamp) OVER (PARTITION BY user_id ORDER BY request_timestamp) AS prev_ride_ts,
    LEAD(request_timestamp) OVER (PARTITION BY user_id ORDER BY request_timestamp) AS next_ride_ts,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY request_timestamp) AS ride_seq
FROM warehouse.fact_rides
WHERE is_completed
LIMIT 200;
