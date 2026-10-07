{{ config(materialized='table') }}

select
    md5(cast(city_id as text)) as city_key,
    city_id,
    city_name,
    country,
    latitude,
    longitude,
    timezone,
    population_tier,
    is_active
from {{ ref('stg_cities') }}
