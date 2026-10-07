{{ config(materialized='table') }}

select
    c.city_id,
    c.city_name,
    count(*) as total_rides,
    count(*) filter (where f.is_completed) as completed_rides,
    round(100.0 * count(*) filter (where f.is_completed) / nullif(count(*), 0), 2) as completion_rate,
    round(100.0 * count(*) filter (where f.is_cancelled) / nullif(count(*), 0), 2) as cancellation_rate,
    round(sum(f.total_fare) filter (where f.is_completed)::numeric, 2) as total_revenue,
    round(avg(f.total_fare) filter (where f.is_completed)::numeric, 2) as average_fare,
    round(avg(f.distance_km) filter (where f.is_completed)::numeric, 2) as average_distance,
    round(avg(f.surge_multiplier)::numeric, 2) as average_surge
from {{ ref('fact_rides') }} f
join {{ ref('dim_city') }} c on f.city_key = c.city_key
group by c.city_id, c.city_name
