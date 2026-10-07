{{ config(materialized='table') }}

select
    md5(cast(promotion_id as text)) as promotion_key,
    promotion_id,
    promotion_code,
    promotion_type,
    discount_percentage,
    maximum_discount,
    start_date,
    end_date,
    target_user_type
from {{ ref('stg_promotions') }}
