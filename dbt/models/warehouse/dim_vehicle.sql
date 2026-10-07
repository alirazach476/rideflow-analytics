{{ config(materialized='table') }}

select
    md5(cast(vehicle_id as text)) as vehicle_key,
    vehicle_id,
    driver_id,
    vehicle_type,
    make,
    model,
    model_year,
    city_id,
    fuel_type,
    capacity,
    status
from {{ ref('stg_vehicles') }}
