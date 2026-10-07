# RideFlow Business Insights

Generated from the live PostgreSQL warehouse. Numbers are not invented.

> Analytical anomaly counts are screening signals, not fraud confirmations.

## Top Revenue City

```
{'city_name': 'Karachi', 'total_revenue': Decimal('116363.68'), 'cancellation_rate': Decimal('22.37')}
```

## Highest Cancel City

```
{'city_name': 'Peshawar', 'cancellation_rate': Decimal('26.37'), 'total_revenue': Decimal('23767.65')}
```

## Busiest Hour

```
{'hour': 8, 'rides': 103}
```

## Surge Vs Metrics

```
{'surge_multiplier': 1.0, 'revenue': Decimal('105858.98'), 'completion_rate': Decimal('70.33'), 'cancellation_rate': Decimal('22.01'), 'ride_demand': 418}
{'surge_multiplier': 1.2, 'revenue': Decimal('251780.06'), 'completion_rate': Decimal('71.93'), 'cancellation_rate': Decimal('20.17'), 'ride_demand': 823}
{'surge_multiplier': 1.5, 'revenue': Decimal('269621.07'), 'completion_rate': Decimal('70.85'), 'cancellation_rate': Decimal('22.18'), 'ride_demand': 717}
{'surge_multiplier': 2.0, 'revenue': Decimal('26797.32'), 'completion_rate': Decimal('72.50'), 'cancellation_rate': Decimal('17.50'), 'ride_demand': 40}
{'surge_multiplier': 2.5, 'revenue': Decimal('1714.81'), 'completion_rate': Decimal('100.00'), 'cancellation_rate': Decimal('0.00'), 'ride_demand': 2}
```

## Top Vehicle

```
{'vehicle_type': 'Sedan', 'completed_rides': 415, 'revenue': Decimal('187047.42')}
```

## Top Driver Util

```
{'driver_id': 16, 'revenue_per_online_hour': Decimal('3326.51'), 'rides_per_online_hour': Decimal('3.563')}
{'driver_id': 2, 'revenue_per_online_hour': Decimal('2625.59'), 'rides_per_online_hour': Decimal('5.217')}
{'driver_id': 45, 'revenue_per_online_hour': Decimal('2017.97'), 'rides_per_online_hour': Decimal('4.842')}
{'driver_id': 49, 'revenue_per_online_hour': Decimal('1265.28'), 'rides_per_online_hour': Decimal('2.729')}
{'driver_id': 11, 'revenue_per_online_hour': Decimal('987.16'), 'rides_per_online_hour': Decimal('1.388')}
```

## Segment Revenue

```
{'customer_segment': 'Inactive', 'users': 318, 'spend': Decimal('303250.94')}
{'customer_segment': 'Low Activity', 'users': 135, 'spend': Decimal('192288.05')}
{'customer_segment': 'Medium Activity', 'users': 47, 'spend': Decimal('160233.25')}
```

## Demand Pressure

```
{'demand_pressure_band': 'Severe Demand Pressure', 'buckets': 2479}
{'demand_pressure_band': 'Balanced', 'buckets': 1}
```

## Payment Failures

```
{'payment_method': 'Debit Card', 'failure_rate': Decimal('4.29'), 'payment_count': 210}
{'payment_method': 'Cash', 'failure_rate': Decimal('4.21'), 'payment_count': 522}
{'payment_method': 'Mobile Wallet', 'failure_rate': Decimal('3.55'), 'payment_count': 366}
{'payment_method': 'Credit Card', 'failure_rate': Decimal('2.32'), 'payment_count': 259}
{'payment_method': 'Bank Transfer', 'failure_rate': Decimal('1.49'), 'payment_count': 67}
```

## Anomaly Counts

```
{'severity': 'Low', 'n': 29}
{'severity': 'Medium', 'n': 18}
{'severity': 'High', 'n': 2}
```
