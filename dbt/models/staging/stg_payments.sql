{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'payments') }}
),
cleaned as (
    select
        payment_id::integer as payment_id,
        ride_id::integer as ride_id,
        user_id::integer as user_id,
        payment_timestamp::timestamp as payment_timestamp,
        initcap(trim(payment_method)) as payment_method,
        amount::double precision as amount,
        case
            when lower(trim(payment_status)) in ('completed', 'failed', 'refunded', 'pending')
                then initcap(trim(payment_status))
            else 'Unknown'
        end as payment_status,
        initcap(trim(transaction_type)) as transaction_type,
        batch_id,
        ingestion_timestamp,
        row_number() over (partition by payment_id order by ingestion_timestamp desc nulls last) as rn
    from source
    where payment_id is not null
)
select * from cleaned where rn = 1
