# RideFlow Data Dictionary

Column reference for major **raw**, **warehouse**, and **audit** tables. Staging views mirror raw columns with typed equivalents.

Types shown are effective warehouse types; raw layer uses permissive `TEXT` where noted.

---

## raw.rides

Central operational event table (CSV landing).

| Column | Data Type | Description | Nullable | PK/FK | Example |
|--------|-----------|-------------|----------|-------|---------|
| ride_id | INTEGER | Unique ride identifier | No | PK | `100042` |
| request_id | TEXT | External request UUID | Yes | | `REQ-a1b2c3` |
| user_id | INTEGER | Rider | No | FK → users | `5012` |
| driver_id | INTEGER | Assigned driver | Yes | FK → drivers | `883` |
| vehicle_id | INTEGER | Vehicle used | Yes | FK → vehicles | `1204` |
| city_id | INTEGER | Operating city | No | FK → cities | `1` |
| pickup_zone_id | INTEGER | Origin zone | Yes | FK → zones | `14` |
| dropoff_zone_id | INTEGER | Destination zone | Yes | FK → zones | `27` |
| request_timestamp | TEXT | Ride requested (raw) | No | | `2024-06-15 08:32:00` |
| accepted_timestamp | TEXT | Driver accepted | Yes | | `2024-06-15 08:34:12` |
| pickup_timestamp | TEXT | Passenger picked up | Yes | | `2024-06-15 08:41:00` |
| dropoff_timestamp | TEXT | Ride ended | Yes | | `2024-06-15 09:05:00` |
| ride_status | TEXT | Lifecycle status | No | | `Completed` |
| distance_km | DOUBLE PRECISION | Trip distance | Yes | | `12.4` |
| duration_minutes | DOUBLE PRECISION | Trip duration | Yes | | `24.0` |
| base_fare | DOUBLE PRECISION | Base component | Yes | | `70.0` |
| surge_multiplier | DOUBLE PRECISION | Surge factor (≥1) | Yes | | `1.5` |
| booking_fee | DOUBLE PRECISION | Platform fee | Yes | | `12.0` |
| toll_amount | DOUBLE PRECISION | Tolls | Yes | | `0.0` |
| discount_amount | DOUBLE PRECISION | Promo discount | Yes | | `25.0` |
| tax_amount | DOUBLE PRECISION | Tax (8%) | Yes | | `18.50` |
| total_fare | DOUBLE PRECISION | Final fare (RFU) | Yes | | `285.50` |
| payment_method | TEXT | Payment type | Yes | | `Mobile Wallet` |
| cancellation_reason | TEXT | If cancelled | Yes | | `Long ETA` |
| cancelled_by | TEXT | Rider or Driver | Yes | | `Rider` |
| updated_at | TEXT | Last change (incremental) | Yes | | `2024-06-15 09:05:01` |
| source_file | TEXT | Ingestion provenance | Yes | | `data/source/rides.csv` |
| ingestion_timestamp | TIMESTAMP | Load time (UTC) | Yes | | `2025-10-07 12:00:00` |
| batch_id | TEXT | Pipeline batch | Yes | | `20251007T120000Z_a1b2c3d4` |

---

## raw.users

| Column | Data Type | Description | Nullable | PK/FK | Example |
|--------|-----------|-------------|----------|-------|---------|
| user_id | INTEGER | Unique user | No | PK | `5012` |
| first_name | TEXT | Given name (synthetic) | Yes | | `Ayesha` |
| last_name | TEXT | Family name (synthetic) | Yes | | `Khan` |
| gender | TEXT | Gender | Yes | | `Female` |
| date_of_birth | TEXT | DOB | Yes | | `1995-03-12` |
| registration_date | TEXT | Signup date | No | | `2024-01-15` |
| city_id | INTEGER | Home city | No | FK → cities | `1` |
| user_type | TEXT | Segment | No | | `Frequent` |
| status | TEXT | Account status | No | | `Active` |
| signup_channel | TEXT | Acquisition channel | Yes | | `Referral` |
| updated_at | TEXT | SCD change marker | Yes | | `2024-06-01` |
| source_file | TEXT | Provenance | Yes | | |
| ingestion_timestamp | TIMESTAMP | Load time | Yes | | |
| batch_id | TEXT | Batch ID | Yes | | |

---

## raw.drivers

| Column | Data Type | Description | Nullable | PK/FK | Example |
|--------|-----------|-------------|----------|-------|---------|
| driver_id | INTEGER | Unique driver | No | PK | `883` |
| first_name | TEXT | Given name | Yes | | `Hassan` |
| last_name | TEXT | Family name | Yes | | `Ali` |
| gender | TEXT | Gender | Yes | | `Male` |
| date_of_birth | TEXT | DOB | Yes | | `1988-07-22` |
| registration_date | TEXT | Join date | No | | `2023-11-01` |
| city_id | INTEGER | Base city | No | FK | `2` |
| driver_type | TEXT | Employment type | Yes | | `Full-Time` |
| status | TEXT | Account status | No | | `Active` |
| rating | DOUBLE PRECISION | Average rating | No | | `4.7` |
| total_rides | INTEGER | Lifetime rides | Yes | | `1250` |
| updated_at | TEXT | Change marker | Yes | | |
| source_file | TEXT | Provenance | Yes | | |
| ingestion_timestamp | TIMESTAMP | Load time | Yes | | |
| batch_id | TEXT | Batch ID | Yes | | |

---

## raw.payments

| Column | Data Type | Description | Nullable | PK/FK | Example |
|--------|-----------|-------------|----------|-------|---------|
| payment_id | INTEGER | Payment ID | No | PK | `90001` |
| ride_id | INTEGER | Related ride | No | FK → rides | `100042` |
| user_id | INTEGER | Payer | No | FK → users | `5012` |
| payment_timestamp | TEXT | Payment time | Yes | | `2024-06-15 09:06:00` |
| payment_method | TEXT | Method | Yes | | `Cash` |
| amount | DOUBLE PRECISION | Amount (RFU) | No | | `285.50` |
| payment_status | TEXT | Status | No | | `Completed` |
| transaction_type | TEXT | Type | Yes | | `Ride Payment` |
| source_file | TEXT | Provenance | Yes | | |
| ingestion_timestamp | TIMESTAMP | Load time | Yes | | |
| batch_id | TEXT | Batch ID | Yes | | |

---

## warehouse.fact_rides

**Grain: One row = one ride request/event.**

| Column | Data Type | Description | Nullable | PK/FK | Example |
|--------|-----------|-------------|----------|-------|---------|
| ride_key | TEXT | Surrogate PK | No | PK | `md5 hash` |
| ride_id | INTEGER | Business key | No | | `100042` |
| date_key | INTEGER | Request date (YYYYMMDD) | Yes | FK → dim_date | `20240615` |
| time_key | INTEGER | Request minute of day | Yes | FK → dim_time | `512` |
| user_key | TEXT | Rider dimension | Yes | FK → dim_user | |
| driver_key | TEXT | Driver dimension | Yes | FK → dim_driver | |
| vehicle_key | TEXT | Vehicle dimension | Yes | FK → dim_vehicle | |
| city_key | TEXT | City dimension | Yes | FK → dim_city | |
| pickup_zone_key | TEXT | Pickup zone | Yes | FK → dim_zone | |
| dropoff_zone_key | TEXT | Dropoff zone | Yes | FK → dim_zone | |
| status_key | TEXT | Status dimension | Yes | FK → dim_ride_status | |
| request_timestamp | TIMESTAMP | Request time | Yes | | |
| accepted_timestamp | TIMESTAMP | Accepted time | Yes | | |
| pickup_timestamp | TIMESTAMP | Pickup time | Yes | | |
| dropoff_timestamp | TIMESTAMP | Dropoff time | Yes | | |
| distance_km | NUMERIC | Distance | Yes | | `12.4` |
| duration_minutes | NUMERIC | Duration | Yes | | `24.0` |
| base_fare | NUMERIC | Base fare | Yes | | |
| surge_multiplier | NUMERIC | Surge | Yes | | `1.5` |
| booking_fee | NUMERIC | Booking fee | Yes | | |
| toll_amount | NUMERIC | Tolls | Yes | | |
| discount_amount | NUMERIC | Discount | Yes | | |
| tax_amount | NUMERIC | Tax | Yes | | |
| total_fare | NUMERIC | Total fare | Yes | | `285.50` |
| payment_method | TEXT | Degenerate dim | Yes | | |
| cancellation_reason | TEXT | Cancel reason | Yes | | |
| cancelled_by | TEXT | Who cancelled | Yes | | |
| user_id | INTEGER | Natural key | Yes | | |
| driver_id | INTEGER | Natural key | Yes | | |
| vehicle_id | INTEGER | Natural key | Yes | | |
| city_id | INTEGER | Natural key | Yes | | |
| pickup_zone_id | INTEGER | Natural key | Yes | | |
| dropoff_zone_id | INTEGER | Natural key | Yes | | |
| ride_status | TEXT | Status label | Yes | | `Completed` |
| is_completed | BOOLEAN | Completed flag | Yes | | `TRUE` |
| is_cancelled | BOOLEAN | Cancelled flag | Yes | | `FALSE` |

---

## warehouse.dim_user (SCD Type 2)

| Column | Data Type | Description | Nullable | PK/FK | Example |
|--------|-----------|-------------|----------|-------|---------|
| user_key | TEXT | Surrogate PK (per version) | No | PK | |
| user_id | INTEGER | Business key | No | | `5012` |
| first_name | TEXT | Name | Yes | | |
| last_name | TEXT | Name | Yes | | |
| gender | TEXT | Gender | Yes | | |
| date_of_birth | DATE | DOB | Yes | | |
| registration_date | DATE | Signup | Yes | | |
| city_id | INTEGER | City | Yes | FK | |
| user_type | TEXT | Segment | Yes | | `Premium` |
| status | TEXT | Status | Yes | | `Active` |
| signup_channel | TEXT | Channel | Yes | | |
| effective_date | TIMESTAMP | Version start | No | | `2024-01-15` |
| expiration_date | TIMESTAMP | Version end | No | | `9999-12-31` |
| is_current | BOOLEAN | Current row | No | | `TRUE` |
| updated_at | TIMESTAMP | Source update | Yes | | |

---

## warehouse.dim_date

| Column | Data Type | Description | Nullable | PK/FK | Example |
|--------|-----------|-------------|----------|-------|---------|
| date_key | INTEGER | YYYYMMDD | No | PK | `20240615` |
| full_date | DATE | Calendar date | No | | `2024-06-15` |
| day | INTEGER | Day of month | Yes | | `15` |
| day_name | TEXT | Weekday name | Yes | | `Saturday` |
| week | INTEGER | ISO week | Yes | | `24` |
| week_of_year | INTEGER | Week number | Yes | | `24` |
| month | INTEGER | Month | Yes | | `6` |
| month_name | TEXT | Month name | Yes | | `June` |
| quarter | INTEGER | Quarter | Yes | | `2` |
| year | INTEGER | Year | Yes | | `2024` |
| is_weekend | BOOLEAN | Sat/Sun | Yes | | `TRUE` |
| is_month_start | BOOLEAN | First of month | Yes | | `FALSE` |
| is_month_end | BOOLEAN | Last of month | Yes | | `FALSE` |

---

## warehouse.dim_time

| Column | Data Type | Description | Nullable | PK/FK | Example |
|--------|-----------|-------------|----------|-------|---------|
| time_key | INTEGER | Minute of day (0–1439) | No | PK | `512` |
| hour | INTEGER | Hour (0–23) | Yes | | `8` |
| minute | INTEGER | Minute (0–59) | Yes | | `32` |
| hour_of_day | INTEGER | Same as hour | Yes | | `8` |
| time_period | TEXT | Day part | Yes | | `Morning` |
| peak_period | TEXT | Peak classification | Yes | | `Morning Peak` |

---

## warehouse.fact_payments

| Column | Data Type | Description | Nullable | PK/FK | Example |
|--------|-----------|-------------|----------|-------|---------|
| payment_key | TEXT | Surrogate PK | No | PK | |
| payment_id | INTEGER | Business key | No | | `90001` |
| ride_id | INTEGER | Related ride | Yes | FK | `100042` |
| user_id | INTEGER | Payer | Yes | | |
| date_key | INTEGER | Payment date | Yes | FK → dim_date | |
| payment_method_key | TEXT | Method dim | Yes | FK | |
| payment_timestamp | TIMESTAMP | Payment time | Yes | | |
| payment_method | TEXT | Method label | Yes | | `Cash` |
| amount | NUMERIC | Amount | Yes | | `285.50` |
| payment_status | TEXT | Status | Yes | | `Completed` |
| transaction_type | TEXT | Type | Yes | | `Ride Payment` |

---

## monitoring.ride_anomalies

| Column | Data Type | Description | Nullable | PK/FK | Example |
|--------|-----------|-------------|----------|-------|---------|
| anomaly_id | SERIAL | Auto ID | No | PK | `1` |
| ride_id | INTEGER | Flagged ride | No | FK | `100042` |
| user_id | INTEGER | Rider | Yes | | |
| driver_id | INTEGER | Driver | Yes | | |
| timestamp | TIMESTAMP | Ride time | Yes | | |
| fare | DOUBLE PRECISION | Fare at flag | Yes | | `850.0` |
| rule_based_score | DOUBLE PRECISION | Rule score | Yes | | `3.5` |
| ml_anomaly_score | DOUBLE PRECISION | IF score | Yes | | `0.72` |
| anomaly_reason | TEXT | Human-readable reason | Yes | | `Extremely high fare...` |
| severity | TEXT | Low/Medium/High/Critical | Yes | | `High` |
| detected_at | TIMESTAMP | Detection run time | No | | |

---

## audit.pipeline_watermarks

| Column | Data Type | Description | Nullable | PK/FK | Example |
|--------|-----------|-------------|----------|-------|---------|
| pipeline_name | TEXT | Pipeline identifier | No | PK (composite) | `raw_ingestion` |
| table_name | TEXT | Target table | No | PK (composite) | `rides` |
| watermark_ts | TIMESTAMP | Last processed high-water | No | | |
| batch_id | TEXT | Last batch | Yes | | |
| updated_at | TIMESTAMP | Record update | No | | |

---

## audit.reconciliation_results

| Column | Data Type | Description | Nullable | PK/FK | Example |
|--------|-----------|-------------|----------|-------|---------|
| reconciliation_id | SERIAL | Auto ID | No | PK | |
| run_id | TEXT | Reconciliation run | No | | UUID |
| metric_name | TEXT | Metric compared | No | | `revenue` |
| source_value | DOUBLE PRECISION | Raw/source value | Yes | | `1250000.0` |
| warehouse_value | DOUBLE PRECISION | Warehouse value | Yes | | `1249998.5` |
| difference | DOUBLE PRECISION | wh − source | Yes | | `-1.5` |
| status | TEXT | PASS/WARNING/FAIL | No | | `PASS` |
| checked_at | TIMESTAMP | Check time | No | | |

---

## Additional Raw Tables

| Table | Primary Key | Purpose |
|-------|-------------|---------|
| `raw.cities` | city_id | City reference |
| `raw.zones` | zone_id | Zone within city |
| `raw.vehicles` | vehicle_id | Driver vehicles |
| `raw.driver_sessions` | session_id | Supply-side sessions |
| `raw.ratings` | rating_id | Post-ride ratings |
| `raw.promotions` | promotion_id | Marketing promos |

See `sql/ddl/02_raw_tables.sql` for full column lists.
