{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'drivers') }}
),
deduped as (
    select *,
        row_number() over (partition by driver_id order by ingestion_timestamp desc nulls last) as rn
    from source
)
select
    driver_id::integer as driver_id,
    initcap(trim(first_name)) as first_name,
    initcap(trim(last_name)) as last_name,
    initcap(trim(gender)) as gender,
    date_of_birth::date as date_of_birth,
    registration_date::date as registration_date,
    city_id::integer as city_id,
    initcap(trim(driver_type)) as driver_type,
    initcap(trim(status)) as status,
    round(rating::numeric, 1) as rating,
    coalesce(total_rides, 0)::integer as total_rides,
    coalesce(updated_at::timestamp, registration_date::timestamp) as updated_at,
    batch_id,
    ingestion_timestamp
from deduped
where rn = 1
  and driver_id is not null
