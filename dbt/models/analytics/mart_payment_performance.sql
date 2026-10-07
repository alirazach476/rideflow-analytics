{{ config(materialized='table') }}

select
    payment_method,
    count(*) as payment_count,
    round(sum(amount)::numeric, 2) as payment_value,
    round(100.0 * count(*) filter (where payment_status = 'Completed') / nullif(count(*), 0), 2) as success_rate,
    round(100.0 * count(*) filter (where payment_status = 'Failed') / nullif(count(*), 0), 2) as failure_rate,
    round(sum(amount) filter (where payment_status = 'Refunded')::numeric, 2) as refund_amount,
    round(avg(amount)::numeric, 2) as average_transaction_value,
    round(100.0 * count(*) / sum(count(*)) over (), 2) as method_share_pct
from {{ ref('fact_payments') }}
group by payment_method
