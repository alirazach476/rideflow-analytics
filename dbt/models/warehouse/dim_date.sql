{{ config(materialized='table') }}

-- Comprehensive date dimension covering synthetic RideFlow date range
with bounds as (
    select
        date '2024-01-01' as start_date,
        date '2025-12-31' as end_date
),
spine as (
    select generate_series(start_date, end_date, interval '1 day')::date as full_date
    from bounds
)
select
    to_char(full_date, 'YYYYMMDD')::integer as date_key,
    full_date,
    extract(day from full_date)::integer as day,
    trim(to_char(full_date, 'Day')) as day_name,
    extract(week from full_date)::integer as week,
    extract(week from full_date)::integer as week_of_year,
    extract(month from full_date)::integer as month,
    trim(to_char(full_date, 'Month')) as month_name,
    extract(quarter from full_date)::integer as quarter,
    extract(year from full_date)::integer as year,
    case when extract(isodow from full_date) in (6, 7) then true else false end as is_weekend,
    case when full_date = date_trunc('month', full_date)::date then true else false end as is_month_start,
    case when full_date = (date_trunc('month', full_date) + interval '1 month' - interval '1 day')::date
         then true else false end as is_month_end
from spine
