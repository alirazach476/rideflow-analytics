{{ config(materialized='table') }}

select
    z.zone_id,
    z.zone_name,
    z.zone_type,
    z.city_id,
    count(*) as pickup_volume,
    round(sum(f.total_fare) filter (where f.is_completed)::numeric, 2) as revenue,
    round(avg(f.total_fare) filter (where f.is_completed)::numeric, 2) as average_fare,
    round(avg(f.distance_km) filter (where f.is_completed)::numeric, 2) as average_distance,
    round(100.0 * count(*) filter (where f.is_cancelled) / nullif(count(*), 0), 2) as cancellation_rate,
    round(avg(f.surge_multiplier)::numeric, 2) as average_surge
from {{ ref('fact_rides') }} f
join {{ ref('dim_zone') }} z on f.pickup_zone_key = z.zone_key
group by z.zone_id, z.zone_name, z.zone_type, z.city_id
