{{ config(materialized='table') }}

with daily as (
    select * from {{ ref('mart_daily_ride_metrics') }}
),
dated as (
    select d.*, dd.year, dd.month, dd.month_name
    from daily d
    join {{ ref('dim_date') }} dd on d.date_key = dd.date_key
)
select
    year,
    month,
    month_name,
    sum(total_rides) as total_rides,
    sum(completed_rides) as completed_rides,
    sum(cancelled_rides) as cancelled_rides,
    round(100.0 * sum(completed_rides) / nullif(sum(total_rides), 0), 2) as completion_rate,
    round(sum(total_revenue)::numeric, 2) as total_revenue,
    round(avg(average_fare)::numeric, 2) as average_fare,
    lag(sum(total_revenue)) over (order by year, month) as prev_month_revenue,
    round(
        100.0 * (sum(total_revenue) - lag(sum(total_revenue)) over (order by year, month))
        / nullif(lag(sum(total_revenue)) over (order by year, month), 0)
    , 2) as revenue_growth_mom
from dated
group by year, month, month_name
