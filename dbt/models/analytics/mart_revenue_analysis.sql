{{ config(materialized='table') }}

select
    dd.year,
    dd.month,
    dd.full_date,
    f.city_id,
    f.payment_method,
    v.vehicle_type,
    count(*) filter (where f.is_completed) as completed_rides,
    round(sum(f.total_fare) filter (where f.is_completed)::numeric, 2) as gross_booking_value,
    round(sum(f.total_fare - coalesce(f.discount_amount, 0) - coalesce(f.tax_amount, 0))
          filter (where f.is_completed)::numeric, 2) as net_revenue,
    round(avg(f.total_fare) filter (where f.is_completed)::numeric, 2) as average_revenue_per_ride,
    count(distinct case when f.is_completed then f.driver_id end) as active_drivers,
    count(distinct case when f.is_completed then f.user_id end) as active_users
from {{ ref('fact_rides') }} f
join {{ ref('dim_date') }} dd on f.date_key = dd.date_key
left join {{ ref('dim_vehicle') }} v on f.vehicle_key = v.vehicle_key
group by 1,2,3,4,5,6
