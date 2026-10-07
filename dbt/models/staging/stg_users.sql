{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'users') }}
),
deduped as (
    select *,
        row_number() over (partition by user_id order by ingestion_timestamp desc nulls last) as rn
    from source
)
select
    user_id::integer as user_id,
    initcap(trim(first_name)) as first_name,
    initcap(trim(last_name)) as last_name,
    initcap(trim(gender)) as gender,
    date_of_birth::date as date_of_birth,
    registration_date::date as registration_date,
    city_id::integer as city_id,
    initcap(trim(user_type)) as user_type,
    initcap(trim(status)) as status,
    initcap(trim(signup_channel)) as signup_channel,
    coalesce(updated_at::timestamp, registration_date::timestamp) as updated_at,
    batch_id,
    ingestion_timestamp
from deduped
where rn = 1
  and user_id is not null
