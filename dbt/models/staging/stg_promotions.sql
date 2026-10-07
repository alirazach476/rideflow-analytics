{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'promotions') }}
),
deduped as (
    select *,
        row_number() over (partition by promotion_id order by ingestion_timestamp desc nulls last) as rn
    from source
)
select
    promotion_id::integer as promotion_id,
    upper(trim(promotion_code)) as promotion_code,
    initcap(trim(promotion_type)) as promotion_type,
    discount_percentage::double precision as discount_percentage,
    maximum_discount::double precision as maximum_discount,
    start_date::date as start_date,
    end_date::date as end_date,
    initcap(trim(target_user_type)) as target_user_type,
    batch_id,
    ingestion_timestamp
from deduped
where rn = 1
  and promotion_id is not null
