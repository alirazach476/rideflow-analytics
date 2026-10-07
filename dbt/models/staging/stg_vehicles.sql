{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'vehicles') }}
),
deduped as (
    select *,
        row_number() over (partition by vehicle_id order by ingestion_timestamp desc nulls last) as rn
    from source
)
select
    vehicle_id::integer as vehicle_id,
    driver_id::integer as driver_id,
    initcap(trim(vehicle_type)) as vehicle_type,
    make,
    model,
    model_year::integer as model_year,
    city_id::integer as city_id,
    initcap(trim(fuel_type)) as fuel_type,
    capacity::integer as capacity,
    initcap(trim(status)) as status,
    batch_id,
    ingestion_timestamp
from deduped
where rn = 1
  and vehicle_id is not null
