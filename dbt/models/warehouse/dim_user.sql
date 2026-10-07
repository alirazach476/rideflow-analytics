{{ config(materialized='table') }}

/*
  SCD Type 2 for users.
  Grain: one row per user_id + version (city_id / user_type / status change).
  For initial load we create a single current version per user.
  Historical changes are applied via incremental SCD logic in macros / future loads
  using effective_date / expiration_date / is_current.
*/

select
    md5(cast(user_id as text) || '|' || cast(registration_date as text)) as user_key,
    user_id,
    first_name,
    last_name,
    gender,
    date_of_birth,
    registration_date,
    city_id,
    user_type,
    status,
    signup_channel,
    registration_date::timestamp as effective_date,
    timestamp '9999-12-31 00:00:00' as expiration_date,
    true as is_current,
    updated_at
from {{ ref('stg_users') }}
