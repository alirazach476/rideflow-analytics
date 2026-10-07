{{ config(materialized='table') }}

select
    f.city_id,
    c.city_name,
    extract(hour from f.request_timestamp)::integer as hour_of_day,
    v.vehicle_type,
    f.surge_multiplier,
    u.user_type,
    d.driver_type,
    f.cancelled_by,
    f.cancellation_reason,
    count(*) as cancellations
from {{ ref('fact_rides') }} f
left join {{ ref('dim_city') }} c on f.city_key = c.city_key
left join {{ ref('dim_vehicle') }} v on f.vehicle_key = v.vehicle_key
left join {{ ref('dim_user') }} u on f.user_key = u.user_key
left join {{ ref('dim_driver') }} d on f.driver_key = d.driver_key
where f.is_cancelled
group by 1,2,3,4,5,6,7,8,9
