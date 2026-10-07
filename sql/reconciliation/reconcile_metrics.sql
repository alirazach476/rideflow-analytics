-- Manual reconciliation queries (also automated in src/transformation/reconcile.py)

SELECT 'raw_ride_count' AS metric, COUNT(DISTINCT ride_id)::FLOAT AS value FROM raw.rides
UNION ALL
SELECT 'warehouse_ride_count', COUNT(*)::FLOAT FROM warehouse.fact_rides
UNION ALL
SELECT 'raw_completed', COUNT(DISTINCT ride_id)::FLOAT FROM raw.rides WHERE LOWER(ride_status)='completed'
UNION ALL
SELECT 'warehouse_completed', COUNT(*)::FLOAT FROM warehouse.fact_rides WHERE is_completed
UNION ALL
SELECT 'raw_revenue', COALESCE(SUM(total_fare),0) FROM raw.rides WHERE LOWER(ride_status)='completed'
UNION ALL
SELECT 'warehouse_revenue', COALESCE(SUM(total_fare),0) FROM warehouse.fact_rides WHERE is_completed;
