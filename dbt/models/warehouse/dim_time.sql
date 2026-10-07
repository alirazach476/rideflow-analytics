{{ config(materialized='table') }}

-- Minute-level time dimension (0–1439)
with spine as (
    select generate_series(0, 1439) as minute_of_day
)
select
    minute_of_day as time_key,
    minute_of_day / 60 as hour,
    minute_of_day % 60 as minute,
    minute_of_day / 60 as hour_of_day,
    case
        when minute_of_day / 60 between 0 and 4 then 'Late Night'
        when minute_of_day / 60 between 5 and 11 then 'Morning'
        when minute_of_day / 60 between 12 and 16 then 'Afternoon'
        when minute_of_day / 60 between 17 and 20 then 'Evening'
        else 'Night'
    end as time_period,
    case
        when minute_of_day / 60 between 7 and 9 then 'Morning Peak'
        when minute_of_day / 60 between 17 and 20 then 'Evening Peak'
        when minute_of_day / 60 between 0 and 4 then 'Late Night'
        else 'Off Peak'
    end as peak_period
from spine
