{{ config(materialized='table') }}

/*
  Grain: ONE ROW = ONE RIDE REQUEST / EVENT (ride_id).
  See docs/data_model.md
*/

with rides as (
    select * from {{ ref('stg_rides') }}
),
users as (
    select * from {{ ref('dim_user') }} where is_current
),
drivers as (
    select * from {{ ref('dim_driver') }}
),
vehicles as (
    select * from {{ ref('dim_vehicle') }}
),
cities as (
    select * from {{ ref('dim_city') }}
),
zones as (
    select * from {{ ref('dim_zone') }}
),
statuses as (
    select * from {{ ref('dim_ride_status') }}
)
select
    md5(cast(r.ride_id as text)) as ride_key,
    r.ride_id,
    to_char(r.request_timestamp::date, 'YYYYMMDD')::integer as date_key,
    (extract(hour from r.request_timestamp)::integer * 60
        + extract(minute from r.request_timestamp)::integer) as time_key,
    u.user_key,
    d.driver_key,
    v.vehicle_key,
    c.city_key,
    pz.zone_key as pickup_zone_key,
    dz.zone_key as dropoff_zone_key,
    s.status_key,
    r.request_timestamp,
    r.accepted_timestamp,
    r.pickup_timestamp,
    r.dropoff_timestamp,
    r.distance_km,
    r.duration_minutes,
    r.base_fare,
    r.surge_multiplier,
    r.booking_fee,
    r.toll_amount,
    r.discount_amount,
    r.tax_amount,
    r.total_fare,
    r.payment_method,
    r.cancellation_reason,
    r.cancelled_by,
    r.user_id,
    r.driver_id,
    r.vehicle_id,
    r.city_id,
    r.pickup_zone_id,
    r.dropoff_zone_id,
    r.ride_status,
    (r.ride_status = 'Completed') as is_completed,
    (r.ride_status in ('Rider_Cancelled', 'Driver_Cancelled')) as is_cancelled
from rides r
left join users u on r.user_id = u.user_id
left join drivers d on r.driver_id = d.driver_id
left join vehicles v on r.vehicle_id = v.vehicle_id
left join cities c on r.city_id = c.city_id
left join zones pz on r.pickup_zone_id = pz.zone_id
left join zones dz on r.dropoff_zone_id = dz.zone_id
left join statuses s on r.ride_status = s.ride_status
