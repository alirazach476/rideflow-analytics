{{ config(materialized='table') }}

select
    md5(cast(s.session_id as text)) as session_key,
    s.session_id,
    s.driver_id,
    d.driver_key,
    s.city_id,
    c.city_key,
    s.zone_id,
    z.zone_key,
    to_char(s.session_start::date, 'YYYYMMDD')::integer as date_key,
    s.session_start,
    s.session_end,
    s.online_minutes,
    s.online_hours,
    s.rides_completed,
    case when s.online_hours > 0
         then round(s.rides_completed::numeric / s.online_hours, 3)
         else 0 end as rides_per_online_hour
from {{ ref('stg_driver_sessions') }} s
left join {{ ref('dim_driver') }} d on s.driver_id = d.driver_id
left join {{ ref('dim_city') }} c on s.city_id = c.city_id
left join {{ ref('dim_zone') }} z on s.zone_id = z.zone_id
