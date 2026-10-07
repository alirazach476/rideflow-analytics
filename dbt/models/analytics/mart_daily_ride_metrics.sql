{{ config(materialized='table') }}

select
    date_key,
    count(*) as total_rides,
    count(*) filter (where is_completed) as completed_rides,
    count(*) filter (where is_cancelled) as cancelled_rides,
    round(100.0 * count(*) filter (where is_completed) / nullif(count(*), 0), 2) as completion_rate,
    round(100.0 * count(*) filter (where is_cancelled) / nullif(count(*), 0), 2) as cancellation_rate,
    round(sum(total_fare) filter (where is_completed)::numeric, 2) as total_revenue,
    round(avg(total_fare) filter (where is_completed)::numeric, 2) as average_fare,
    round(avg(distance_km) filter (where is_completed)::numeric, 2) as average_distance,
    round(avg(duration_minutes) filter (where is_completed)::numeric, 2) as average_duration,
    round(
        (sum(total_fare) filter (where is_completed) / nullif(sum(distance_km) filter (where is_completed), 0))::numeric
    , 2) as average_fare_per_km,
    round(
        (sum(total_fare) filter (where is_completed) / nullif(sum(duration_minutes) filter (where is_completed), 0))::numeric
    , 2) as average_fare_per_minute
from {{ ref('fact_rides') }}
group by date_key
