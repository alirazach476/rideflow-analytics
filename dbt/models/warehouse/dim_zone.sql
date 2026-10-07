{{ config(materialized='table') }}

select
    md5(cast(zone_id as text)) as zone_key,
    zone_id,
    city_id,
    zone_name,
    zone_type,
    latitude_center,
    longitude_center,
    demand_index
from {{ ref('stg_zones') }}
