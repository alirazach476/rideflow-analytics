{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'ratings') }}
),
deduped as (
    select *,
        row_number() over (partition by rating_id order by ingestion_timestamp desc nulls last) as rn
    from source
)
select
    rating_id::integer as rating_id,
    ride_id::integer as ride_id,
    user_id::integer as user_id,
    driver_id::integer as driver_id,
    initcap(trim(rating_from)) as rating_from,
    initcap(trim(rating_to)) as rating_to,
    rating::integer as rating,
    rating_timestamp::timestamp as rating_timestamp,
    comment_category,
    batch_id,
    ingestion_timestamp
from deduped
where rn = 1
  and rating_id is not null
  and rating between 1 and 5
