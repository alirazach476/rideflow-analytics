-- Practical indexes for RideFlow analytical workloads
-- Only indexes with clear query purpose.

-- Raw / operational
CREATE INDEX IF NOT EXISTS idx_raw_rides_request_ts ON raw.rides ((request_timestamp));
CREATE INDEX IF NOT EXISTS idx_raw_rides_user ON raw.rides (user_id);
CREATE INDEX IF NOT EXISTS idx_raw_rides_driver ON raw.rides (driver_id);
CREATE INDEX IF NOT EXISTS idx_raw_rides_city ON raw.rides (city_id);
CREATE INDEX IF NOT EXISTS idx_raw_rides_pickup_zone ON raw.rides (pickup_zone_id);
CREATE INDEX IF NOT EXISTS idx_raw_rides_dropoff_zone ON raw.rides (dropoff_zone_id);
CREATE INDEX IF NOT EXISTS idx_raw_payments_ride ON raw.payments (ride_id);
CREATE INDEX IF NOT EXISTS idx_raw_sessions_driver ON raw.driver_sessions (driver_id);

-- Warehouse facts (created after dbt build)
CREATE INDEX IF NOT EXISTS idx_fact_rides_date ON warehouse.fact_rides (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_rides_city ON warehouse.fact_rides (city_id);
CREATE INDEX IF NOT EXISTS idx_fact_rides_user ON warehouse.fact_rides (user_id);
CREATE INDEX IF NOT EXISTS idx_fact_rides_driver ON warehouse.fact_rides (driver_id);
CREATE INDEX IF NOT EXISTS idx_fact_rides_status ON warehouse.fact_rides (is_completed, is_cancelled);
CREATE INDEX IF NOT EXISTS idx_fact_payments_method ON warehouse.fact_payments (payment_method);
CREATE INDEX IF NOT EXISTS idx_fact_sessions_driver ON warehouse.fact_driver_sessions (driver_id);
