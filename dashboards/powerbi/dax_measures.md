# RideFlow DAX Measures

Base table for fact measures: `fact_rides` (or import marts and adapt).

```dax
Total Rides = COUNTROWS ( fact_rides )

Completed Rides =
CALCULATE ( COUNTROWS ( fact_rides ), fact_rides[is_completed] = TRUE )

Cancelled Rides =
CALCULATE ( COUNTROWS ( fact_rides ), fact_rides[is_cancelled] = TRUE )

Completion Rate =
DIVIDE ( [Completed Rides], [Total Rides] )

Cancellation Rate =
DIVIDE ( [Cancelled Rides], [Total Rides] )

Total Revenue =
CALCULATE ( SUM ( fact_rides[total_fare] ), fact_rides[is_completed] = TRUE )

Average Fare =
CALCULATE ( AVERAGE ( fact_rides[total_fare] ), fact_rides[is_completed] = TRUE )

Average Distance =
CALCULATE ( AVERAGE ( fact_rides[distance_km] ), fact_rides[is_completed] = TRUE )

Average Duration =
CALCULATE ( AVERAGE ( fact_rides[duration_minutes] ), fact_rides[is_completed] = TRUE )

Active Users =
CALCULATE (
    DISTINCTCOUNT ( fact_rides[user_id] ),
    fact_rides[is_completed] = TRUE
)

Active Drivers =
CALCULATE (
    DISTINCTCOUNT ( fact_rides[driver_id] ),
    fact_rides[is_completed] = TRUE
)

Average Driver Rating =
AVERAGE ( fact_ratings[rating] )

Revenue per Driver =
DIVIDE ( [Total Revenue], [Active Drivers] )

Rides per Driver =
DIVIDE ( [Completed Rides], [Active Drivers] )

Revenue Growth MoM =
VAR CurrentRev = [Total Revenue]
VAR PrevRev =
    CALCULATE ( [Total Revenue], DATEADD ( dim_date[full_date], -1, MONTH ) )
RETURN
    DIVIDE ( CurrentRev - PrevRev, PrevRev )

Ride Growth MoM =
VAR CurrentRides = [Total Rides]
VAR PrevRides =
    CALCULATE ( [Total Rides], DATEADD ( dim_date[full_date], -1, MONTH ) )
RETURN
    DIVIDE ( CurrentRides - PrevRides, PrevRides )

Anomaly Count = COUNTROWS ( ride_anomalies )

Anomaly Rate =
DIVIDE ( [Anomaly Count], [Completed Rides] )
```

Do not hardcode numeric literals into measures; all values come from the model.
