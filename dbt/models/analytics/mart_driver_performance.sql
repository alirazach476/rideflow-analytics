{{ config(materialized='table') }}

with ride_stats as (
    select
        driver_id,
        count(*) as total_assigned_rides,
        count(*) filter (where is_completed) as completed_rides,
        count(*) filter (where ride_status = 'Driver_Cancelled') as driver_cancellations,
        count(*) filter (where ride_status not in ('Requested', 'No_Driver_Available')) as accepted_or_beyond,
        coalesce(sum(total_fare) filter (where is_completed), 0) as revenue_generated,
        avg(distance_km) filter (where is_completed) as average_trip_distance,
        avg(duration_minutes) filter (where is_completed) as average_trip_duration
    from {{ ref('fact_rides') }}
    where driver_id is not null
    group by driver_id
),
sessions as (
    select
        driver_id,
        sum(online_hours) as online_hours,
        sum(rides_completed) as session_rides
    from {{ ref('fact_driver_sessions') }}
    group by driver_id
),
ratings as (
    select driver_id, avg(rating)::numeric as average_rating
    from {{ ref('fact_ratings') }}
    where rating_to = 'Driver'
    group by driver_id
)
select
    d.driver_id,
    d.driver_type,
    d.status,
    d.city_id,
    d.rating as profile_rating,
    coalesce(r.total_assigned_rides, 0) as total_assigned_rides,
    coalesce(r.completed_rides, 0) as completed_rides,
    round(100.0 * r.completed_rides / nullif(r.accepted_or_beyond, 0), 2) as acceptance_completion_rate,
    round(100.0 * r.driver_cancellations / nullif(r.total_assigned_rides, 0), 2) as cancellation_rate,
    round(coalesce(rt.average_rating, d.rating)::numeric, 2) as average_rating,
    round(r.revenue_generated::numeric, 2) as revenue_generated,
    round(s.online_hours::numeric, 2) as online_hours,
    round((r.revenue_generated / nullif(s.online_hours, 0))::numeric, 2) as revenue_per_online_hour,
    round((r.completed_rides::numeric / nullif(s.online_hours, 0)), 3) as rides_per_online_hour,
    round(r.average_trip_distance::numeric, 2) as average_trip_distance,
    round(r.average_trip_duration::numeric, 2) as average_trip_duration,
    row_number() over (order by r.revenue_generated desc nulls last) as revenue_rank,
    rank() over (order by r.revenue_generated desc nulls last) as revenue_rank_with_ties,
    dense_rank() over (order by coalesce(rt.average_rating, d.rating) desc nulls last) as rating_dense_rank
from {{ ref('dim_driver') }} d
left join ride_stats r on d.driver_id = r.driver_id
left join sessions s on d.driver_id = s.driver_id
left join ratings rt on d.driver_id = rt.driver_id
