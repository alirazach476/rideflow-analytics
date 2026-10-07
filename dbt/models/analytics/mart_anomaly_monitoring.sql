{{ config(materialized='table') }}

-- Mirror of monitoring.ride_anomalies for BI consumption (populated by Python job)
select
    anomaly_id,
    ride_id,
    user_id,
    driver_id,
    timestamp,
    fare,
    rule_based_score,
    ml_anomaly_score,
    anomaly_reason,
    severity,
    detected_at
from {{ source('monitoring', 'ride_anomalies') }}
