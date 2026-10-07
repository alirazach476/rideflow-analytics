{{ config(materialized='table') }}

select
    v.vehicle_type,
    count(*) as total_rides,
    count(*) filter (where f.is_completed) as completed_rides,
    round(sum(f.total_fare) filter (where f.is_completed)::numeric, 2) as revenue,
    round(avg(f.total_fare) filter (where f.is_completed)::numeric, 2) as average_fare,
    round(avg(f.distance_km) filter (where f.is_completed)::numeric, 2) as average_distance,
    round(100.0 * count(*) filter (where f.is_cancelled) / nullif(count(*), 0), 2) as cancellation_rate
from {{ ref('fact_rides') }} f
join {{ ref('dim_vehicle') }} v on f.vehicle_key = v.vehicle_key
group by v.vehicle_type
