{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'cities') }}
),
deduped as (
    select
        *,
        row_number() over (partition by city_id order by ingestion_timestamp desc nulls last) as rn
    from source
)
select
    city_id::integer as city_id,
    initcap(trim(city_name)) as city_name,
    upper(trim(country)) as country,
    latitude::double precision as latitude,
    longitude::double precision as longitude,
    timezone,
    population_tier,
    coalesce(is_active, true) as is_active,
    batch_id,
    ingestion_timestamp
from deduped
where rn = 1
  and city_id is not null
