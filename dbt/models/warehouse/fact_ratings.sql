{{ config(materialized='table') }}

select
    md5(cast(r.rating_id as text)) as rating_key,
    r.rating_id,
    r.ride_id,
    r.user_id,
    r.driver_id,
    u.user_key,
    d.driver_key,
    to_char(r.rating_timestamp::date, 'YYYYMMDD')::integer as date_key,
    r.rating_from,
    r.rating_to,
    r.rating,
    r.rating_timestamp,
    r.comment_category
from {{ ref('stg_ratings') }} r
left join {{ ref('dim_user') }} u on r.user_id = u.user_id and u.is_current
left join {{ ref('dim_driver') }} d on r.driver_id = d.driver_id
