{{ config(materialized='view') }}

-- Intermediate: expose fare components for reconciliation / analytics
select
    ride_id,
    vehicle_id,
    distance_km,
    duration_minutes,
    base_fare,
    booking_fee,
    toll_amount,
    discount_amount,
    tax_amount,
    surge_multiplier,
    total_fare,
    is_completed
from {{ ref('fact_rides') }}
where is_completed
