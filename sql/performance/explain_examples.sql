-- Example EXPLAIN plans (run after warehouse is built).
-- Do not fabricate benchmark timings — capture locally with EXPLAIN ANALYZE.

EXPLAIN
SELECT city_id, COUNT(*)
FROM warehouse.fact_rides
WHERE is_completed
GROUP BY city_id;

EXPLAIN ANALYZE
SELECT f.driver_id, SUM(f.total_fare)
FROM warehouse.fact_rides f
WHERE f.is_completed
  AND f.date_key BETWEEN 20240101 AND 20240630
GROUP BY f.driver_id
ORDER BY 2 DESC
LIMIT 20;

-- Partitioning discussion (not enabled by default):
-- For multi-year fact_rides at 10M+ rows, RANGE partition by date_key year/month
-- can improve pruning for dashboard date slicers. Evaluate after measuring
-- EXPLAIN ANALYZE on real local volumes.
