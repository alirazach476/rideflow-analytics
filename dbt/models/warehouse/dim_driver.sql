{{ config(materialized='table') }}

select
    md5(cast(driver_id as text)) as driver_key,
    driver_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    registration_date,
    city_id,
    driver_type,
    status,
    rating,
    total_rides
from {{ ref('stg_drivers') }}
