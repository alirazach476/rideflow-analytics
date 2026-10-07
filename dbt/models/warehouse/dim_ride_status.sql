{{ config(materialized='table') }}

select
    md5(cast(ride_status as text)) as status_key,
    ride_status,
    case
        when ride_status = 'Completed' then 'Completed'
        when ride_status in ('Rider_Cancelled', 'Driver_Cancelled') then 'Cancelled'
        when ride_status = 'No_Driver_Available' then 'Unfulfilled'
        else 'In Progress'
    end as status_group
from (
    select distinct ride_status from {{ ref('stg_rides') }}
) s
