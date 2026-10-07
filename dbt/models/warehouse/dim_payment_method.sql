{{ config(materialized='table') }}

select
    md5(cast(payment_method as text)) as payment_method_key,
    payment_method
from (
    select distinct payment_method
    from {{ ref('stg_payments') }}
    where payment_method is not null
) p
