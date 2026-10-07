{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'zones') }}
),
deduped as (
    select *,
        row_number() over (partition by zone_id order by ingestion_timestamp desc nulls last) as rn
    from source
)
select
    zone_id::integer as zone_id,
    city_id::integer as city_id,
    trim(zone_name) as zone_name,
    initcap(trim(zone_type)) as zone_type,
    latitude_center::double precision as latitude_center,
    longitude_center::double precision as longitude_center,
    demand_index::double precision as demand_index,
    batch_id,
    ingestion_timestamp
from deduped
where rn = 1
  and zone_id is not null
