{{ config(materialized='table') }}

with first_rides as (
    select
        user_id,
        min(request_timestamp)::date as first_ride_date,
        date_trunc('month', min(request_timestamp))::date as first_ride_month
    from {{ ref('fact_rides') }}
    where is_completed
    group by user_id
),
user_signup as (
    select user_id, date_trunc('month', registration_date)::date as signup_month
    from {{ ref('dim_user') }}
    where is_current
),
activity as (
    select
        f.user_id,
        date_trunc('month', f.request_timestamp)::date as activity_month
    from {{ ref('fact_rides') }} f
    where f.is_completed
    group by 1,2
)
select
    s.signup_month,
    fr.first_ride_month,
    count(distinct s.user_id) as cohort_users,
    count(distinct case when a.activity_month = fr.first_ride_month then s.user_id end) as month_0_active,
    count(distinct case when a.activity_month = fr.first_ride_month + interval '1 month' then s.user_id end) as month_1_retained,
    count(distinct case when a.activity_month <= fr.first_ride_date + interval '30 days' then s.user_id end) as retained_30d,
    count(distinct case when a.activity_month <= fr.first_ride_date + interval '60 days' then s.user_id end) as retained_60d,
    count(distinct case when a.activity_month <= fr.first_ride_date + interval '90 days' then s.user_id end) as retained_90d
from user_signup s
left join first_rides fr on s.user_id = fr.user_id
left join activity a on s.user_id = a.user_id
group by s.signup_month, fr.first_ride_month
