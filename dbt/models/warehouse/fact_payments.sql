{{ config(materialized='table') }}

select
    md5(cast(p.payment_id as text)) as payment_key,
    p.payment_id,
    p.ride_id,
    p.user_id,
    to_char(p.payment_timestamp::date, 'YYYYMMDD')::integer as date_key,
    pm.payment_method_key,
    p.payment_timestamp,
    p.payment_method,
    p.amount,
    p.payment_status,
    p.transaction_type
from {{ ref('stg_payments') }} p
left join {{ ref('dim_payment_method') }} pm
    on p.payment_method = pm.payment_method
