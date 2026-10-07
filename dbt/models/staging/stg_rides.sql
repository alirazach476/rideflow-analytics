{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'rides') }}
),
cleaned as (
    select
        ride_id::integer as ride_id,
        request_id,
        user_id::integer as user_id,
        nullif(driver_id, 0)::integer as driver_id,
        nullif(vehicle_id, 0)::integer as vehicle_id,
        city_id::integer as city_id,
        pickup_zone_id::integer as pickup_zone_id,
        dropoff_zone_id::integer as dropoff_zone_id,
        request_timestamp::timestamp as request_timestamp,
        accepted_timestamp::timestamp as accepted_timestamp,
        pickup_timestamp::timestamp as pickup_timestamp,
        dropoff_timestamp::timestamp as dropoff_timestamp,
        -- Normalize intentional capitalization / invalid statuses
        case
            when lower(trim(ride_status)) in ('completed', 'completed') then 'Completed'
            when lower(trim(ride_status)) = 'requested' then 'Requested'
            when lower(trim(ride_status)) = 'accepted' then 'Accepted'
            when lower(trim(ride_status)) in ('driver_cancelled', 'driver cancelled') then 'Driver_Cancelled'
            when lower(trim(ride_status)) in ('rider_cancelled', 'rider cancelled') then 'Rider_Cancelled'
            when lower(trim(ride_status)) in ('no_driver_available', 'no driver available') then 'No_Driver_Available'
            else 'Unknown'
        end as ride_status,
        case when distance_km is not null and distance_km > 0 then distance_km end as distance_km,
        case when duration_minutes is not null and duration_minutes > 0 then duration_minutes end as duration_minutes,
        base_fare,
        greatest(coalesce(surge_multiplier, 1.0), 1.0) as surge_multiplier,
        booking_fee,
        coalesce(toll_amount, 0) as toll_amount,
        greatest(coalesce(discount_amount, 0), 0) as discount_amount,
        tax_amount,
        case when total_fare is not null and total_fare >= 0 then total_fare end as total_fare,
        payment_method,
        cancellation_reason,
        cancelled_by,
        coalesce(updated_at::timestamp, request_timestamp::timestamp) as updated_at,
        batch_id,
        ingestion_timestamp,
        row_number() over (partition by ride_id order by ingestion_timestamp desc nulls last) as rn
    from source
    where ride_id is not null
)
select * from cleaned where rn = 1
