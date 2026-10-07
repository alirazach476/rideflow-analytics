{{ config(materialized='table') }}

select
    surge_multiplier,
    count(*) as ride_demand,
    count(*) filter (where is_completed) as completed_rides,
    round(sum(total_fare) filter (where is_completed)::numeric, 2) as revenue,
    round(avg(total_fare) filter (where is_completed)::numeric, 2) as average_fare,
    round(100.0 * count(*) filter (where is_completed) / nullif(count(*), 0), 2) as completion_rate,
    round(100.0 * count(*) filter (where is_cancelled) / nullif(count(*), 0), 2) as cancellation_rate
from {{ ref('fact_rides') }}
group by surge_multiplier
order by surge_multiplier
