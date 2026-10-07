{{ config(materialized='table') }}

/*
  Hourly supply vs demand.
  demand_supply_ratio = ride_requests / nullif(available_drivers, 0)

  Thresholds (documented):
    Low Demand:            ratio < 0.5
    Balanced:              0.5 <= ratio < 1.5
    High Demand:           1.5 <= ratio < 3.0
    Severe Demand Pressure: ratio >= 3.0
*/

with ride_hours as (
    select
        city_id,
        date_key,
        extract(hour from request_timestamp)::integer as hour_of_day,
        count(*) as ride_requests,
        count(*) filter (where is_completed) as completed_rides
    from {{ ref('fact_rides') }}
    group by 1,2,3
),
session_hours as (
    select
        city_id,
        to_char(session_start::date, 'YYYYMMDD')::integer as date_key,
        extract(hour from session_start)::integer as hour_of_day,
        count(distinct driver_id) as available_drivers,
        sum(online_hours) as driver_online_hours
    from {{ ref('fact_driver_sessions') }}
    group by 1,2,3
)
select
    coalesce(r.city_id, s.city_id) as city_id,
    coalesce(r.date_key, s.date_key) as date_key,
    coalesce(r.hour_of_day, s.hour_of_day) as hour_of_day,
    coalesce(r.ride_requests, 0) as ride_requests,
    coalesce(r.completed_rides, 0) as completed_rides,
    coalesce(s.available_drivers, 0) as available_drivers,
    coalesce(s.available_drivers, 0) as active_drivers,
    round(coalesce(s.driver_online_hours, 0)::numeric, 2) as driver_online_hours,
    round(
        (coalesce(r.ride_requests, 0)::numeric / nullif(s.available_drivers, 0))
    , 3) as demand_supply_ratio,
    case
        when s.available_drivers is null or s.available_drivers = 0 then 'Severe Demand Pressure'
        when (r.ride_requests::numeric / s.available_drivers) < 0.5 then 'Low Demand'
        when (r.ride_requests::numeric / s.available_drivers) < 1.5 then 'Balanced'
        when (r.ride_requests::numeric / s.available_drivers) < 3.0 then 'High Demand'
        else 'Severe Demand Pressure'
    end as demand_pressure_band
from ride_hours r
full outer join session_hours s
    on r.city_id = s.city_id
   and r.date_key = s.date_key
   and r.hour_of_day = s.hour_of_day
