-- Raw layer: minimal transformation, includes ingestion metadata
-- Types are intentionally permissive (TEXT) where source quality varies.

CREATE TABLE IF NOT EXISTS raw.cities (
    city_id             INTEGER,
    city_name           TEXT,
    country             TEXT,
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,
    timezone            TEXT,
    population_tier     TEXT,
    is_active           BOOLEAN,
    source_file         TEXT,
    ingestion_timestamp TIMESTAMP,
    batch_id            TEXT
);

CREATE TABLE IF NOT EXISTS raw.zones (
    zone_id             INTEGER,
    city_id             INTEGER,
    zone_name           TEXT,
    zone_type           TEXT,
    latitude_center     DOUBLE PRECISION,
    longitude_center    DOUBLE PRECISION,
    demand_index        DOUBLE PRECISION,
    source_file         TEXT,
    ingestion_timestamp TIMESTAMP,
    batch_id            TEXT
);

CREATE TABLE IF NOT EXISTS raw.users (
    user_id             INTEGER,
    first_name          TEXT,
    last_name           TEXT,
    gender              TEXT,
    date_of_birth       TEXT,
    registration_date   TEXT,
    city_id             INTEGER,
    user_type           TEXT,
    status              TEXT,
    signup_channel      TEXT,
    updated_at          TEXT,
    source_file         TEXT,
    ingestion_timestamp TIMESTAMP,
    batch_id            TEXT
);

CREATE TABLE IF NOT EXISTS raw.drivers (
    driver_id           INTEGER,
    first_name          TEXT,
    last_name           TEXT,
    gender              TEXT,
    date_of_birth       TEXT,
    registration_date   TEXT,
    city_id             INTEGER,
    driver_type         TEXT,
    status              TEXT,
    rating              DOUBLE PRECISION,
    total_rides         INTEGER,
    updated_at          TEXT,
    source_file         TEXT,
    ingestion_timestamp TIMESTAMP,
    batch_id            TEXT
);

CREATE TABLE IF NOT EXISTS raw.vehicles (
    vehicle_id          INTEGER,
    driver_id           INTEGER,
    vehicle_type        TEXT,
    make                TEXT,
    model               TEXT,
    model_year          INTEGER,
    city_id             INTEGER,
    fuel_type           TEXT,
    capacity            INTEGER,
    status              TEXT,
    source_file         TEXT,
    ingestion_timestamp TIMESTAMP,
    batch_id            TEXT
);

CREATE TABLE IF NOT EXISTS raw.rides (
    ride_id             INTEGER,
    request_id          TEXT,
    user_id             INTEGER,
    driver_id           INTEGER,
    vehicle_id          INTEGER,
    city_id             INTEGER,
    pickup_zone_id      INTEGER,
    dropoff_zone_id     INTEGER,
    request_timestamp   TEXT,
    accepted_timestamp  TEXT,
    pickup_timestamp    TEXT,
    dropoff_timestamp   TEXT,
    ride_status         TEXT,
    distance_km         DOUBLE PRECISION,
    duration_minutes    DOUBLE PRECISION,
    base_fare           DOUBLE PRECISION,
    surge_multiplier    DOUBLE PRECISION,
    booking_fee         DOUBLE PRECISION,
    toll_amount         DOUBLE PRECISION,
    discount_amount     DOUBLE PRECISION,
    tax_amount          DOUBLE PRECISION,
    total_fare          DOUBLE PRECISION,
    payment_method      TEXT,
    cancellation_reason TEXT,
    cancelled_by        TEXT,
    updated_at          TEXT,
    source_file         TEXT,
    ingestion_timestamp TIMESTAMP,
    batch_id            TEXT
);

CREATE TABLE IF NOT EXISTS raw.driver_sessions (
    session_id          INTEGER,
    driver_id           INTEGER,
    city_id             INTEGER,
    zone_id             INTEGER,
    session_start       TEXT,
    session_end         TEXT,
    online_minutes      INTEGER,
    rides_completed     INTEGER,
    source_file         TEXT,
    ingestion_timestamp TIMESTAMP,
    batch_id            TEXT
);

CREATE TABLE IF NOT EXISTS raw.payments (
    payment_id          INTEGER,
    ride_id             INTEGER,
    user_id             INTEGER,
    payment_timestamp   TEXT,
    payment_method      TEXT,
    amount              DOUBLE PRECISION,
    payment_status      TEXT,
    transaction_type    TEXT,
    source_file         TEXT,
    ingestion_timestamp TIMESTAMP,
    batch_id            TEXT
);

CREATE TABLE IF NOT EXISTS raw.ratings (
    rating_id           INTEGER,
    ride_id             INTEGER,
    user_id             INTEGER,
    driver_id           INTEGER,
    rating_from         TEXT,
    rating_to           TEXT,
    rating              INTEGER,
    rating_timestamp    TEXT,
    comment_category    TEXT,
    source_file         TEXT,
    ingestion_timestamp TIMESTAMP,
    batch_id            TEXT
);

CREATE TABLE IF NOT EXISTS raw.promotions (
    promotion_id        INTEGER,
    promotion_code      TEXT,
    promotion_type      TEXT,
    discount_percentage DOUBLE PRECISION,
    maximum_discount    DOUBLE PRECISION,
    start_date          TEXT,
    end_date            TEXT,
    target_user_type    TEXT,
    source_file         TEXT,
    ingestion_timestamp TIMESTAMP,
    batch_id            TEXT
);

CREATE INDEX IF NOT EXISTS idx_raw_rides_request_ts ON raw.rides ((request_timestamp));
CREATE INDEX IF NOT EXISTS idx_raw_rides_user ON raw.rides (user_id);
CREATE INDEX IF NOT EXISTS idx_raw_rides_driver ON raw.rides (driver_id);
CREATE INDEX IF NOT EXISTS idx_raw_rides_city ON raw.rides (city_id);
CREATE INDEX IF NOT EXISTS idx_raw_payments_ride ON raw.payments (ride_id);
CREATE INDEX IF NOT EXISTS idx_raw_sessions_driver ON raw.driver_sessions (driver_id);
