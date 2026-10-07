{{ config(materialized='table') }}

/*
  Customer segments from documented behavioral rules (not hardcoded labels):
  - Inactive:       days_since_last_ride > 90 OR completed_rides = 0
  - Low Activity:   completed_rides between 1 and 5
  - Medium Activity: completed_rides between 6 and 20
  - High Activity:  completed_rides > 20 AND total_spend < 15000
  - Premium:        completed_rides > 20 AND total_spend >= 15000

  days_since_last_ride is measured against the dataset's max ride date
  (not wall-clock current_date) so synthetic historical ranges stay meaningful.
*/

with as_of as (
    select coalesce(max(request_timestamp)::date, current_date) as as_of_date
    from {{ ref('fact_rides') }}
),
ride_stats as (
    select
        user_id,
        count(*) as total_rides,
        count(*) filter (where is_completed) as completed_rides,
        count(*) filter (where is_cancelled) as cancelled_rides,
        coalesce(sum(total_fare) filter (where is_completed), 0) as total_spend,
        avg(total_fare) filter (where is_completed) as average_fare,
        avg(distance_km) filter (where is_completed) as average_distance,
        max(request_timestamp) as last_ride_date
    from {{ ref('fact_rides') }}
    group by user_id
),
ratings as (
    select user_id, avg(rating)::numeric as average_rating_given
    from {{ ref('fact_ratings') }}
    where rating_from = 'User'
    group by user_id
)
select
    u.user_id,
    u.user_type,
    u.status,
    u.city_id,
    u.registration_date,
    coalesce(r.total_rides, 0) as total_rides,
    coalesce(r.completed_rides, 0) as completed_rides,
    coalesce(r.cancelled_rides, 0) as cancelled_rides,
    round(coalesce(r.total_spend, 0)::numeric, 2) as total_spend,
    round(r.average_fare::numeric, 2) as average_fare,
    round(r.average_distance::numeric, 2) as average_distance,
    round(rt.average_rating_given, 2) as average_rating_given,
    r.last_ride_date,
    (a.as_of_date - r.last_ride_date::date) as days_since_last_ride,
    case
        when coalesce(r.completed_rides, 0) = 0
             or (a.as_of_date - r.last_ride_date::date) > 90 then 'Inactive'
        when r.completed_rides between 1 and 5 then 'Low Activity'
        when r.completed_rides between 6 and 20 then 'Medium Activity'
        when r.completed_rides > 20 and r.total_spend >= 15000 then 'Premium'
        when r.completed_rides > 20 then 'High Activity'
        else 'Low Activity'
    end as customer_segment
from {{ ref('dim_user') }} u
cross join as_of a
left join ride_stats r on u.user_id = r.user_id
left join ratings rt on u.user_id = rt.user_id
where u.is_current
