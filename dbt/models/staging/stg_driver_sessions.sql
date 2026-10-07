{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'driver_sessions') }}
),
deduped as (
    select *,
        row_number() over (partition by session_id order by ingestion_timestamp desc nulls last) as rn
    from source
)
select
    session_id::integer as session_id,
    driver_id::integer as driver_id,
    city_id::integer as city_id,
    zone_id::integer as zone_id,
    session_start::timestamp as session_start,
    session_end::timestamp as session_end,
    online_minutes::integer as online_minutes,
    rides_completed::integer as rides_completed,
    round(online_minutes::numeric / 60.0, 2) as online_hours,
    batch_id,
    ingestion_timestamp
from deduped
where rn = 1
  and session_id is not null
