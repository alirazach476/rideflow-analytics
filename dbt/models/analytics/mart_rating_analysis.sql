{{ config(materialized='table') }}

select
    rating_to as rated_entity,
    count(*) as rating_count,
    round(avg(rating)::numeric, 2) as average_rating,
    count(*) filter (where rating = 5) as excellent,
    count(*) filter (where rating = 4) as good,
    count(*) filter (where rating = 3) as average,
    count(*) filter (where rating = 2) as poor,
    count(*) filter (where rating = 1) as very_poor
from {{ ref('fact_ratings') }}
group by rating_to
