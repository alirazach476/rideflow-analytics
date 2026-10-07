# RideFlow Data Model

The RideFlow warehouse implements a **Kimball-style star schema** in PostgreSQL schema `warehouse`, built by dbt from `staging` views sourced from `raw` tables.

---

## Design Principles

1. **Conformed dimensions** — shared keys across facts (date, city, user, driver)
2. **Explicit grain** — documented on every fact table
3. **Surrogate keys** — MD5-based `*_key` columns for warehouse joins
4. **Degenerate dimensions** — natural IDs retained on facts for traceability
5. **SCD Type 2** — `dim_user` preserves history when attributes change

---

## Star Schema Overview

```text
                    dim_date ─────┐
                    dim_time ─────┤
                    dim_user ─────┤
                    dim_driver ───┤
                    dim_vehicle ──┼──► fact_rides ◄── central fact
                    dim_city ─────┤
                    dim_zone ─────┤ (pickup & dropoff)
                    dim_ride_status ┘

                    dim_date ─────┐
                    dim_payment_method ──► fact_payments

                    dim_driver ───┐
                    dim_city ─────┼──► fact_driver_sessions
                    dim_zone ─────┘

                    dim_user ─────┐
                    dim_driver ───┴──► fact_ratings
```

---

## Fact Tables

### fact_rides

| Attribute | Value |
|-----------|-------|
| **Grain** | **One row represents one ride request/event** |
| Natural key | `ride_id` |
| Surrogate key | `ride_key` |
| Source | `stg_rides` joined to dimensions |

Includes all lifecycle statuses (Completed, Cancelled, Requested, etc.). Measures: distance, duration, fare components, surge. Flags: `is_completed`, `is_cancelled`.

### fact_payments

| Attribute | Value |
|-----------|-------|
| **Grain** | One row per payment transaction |
| Natural key | `payment_id` |
| Surrogate key | `payment_key` |

### fact_driver_sessions

| Attribute | Value |
|-----------|-------|
| **Grain** | One row per driver online session |
| Natural key | `session_id` |

### fact_ratings

| Attribute | Value |
|-----------|-------|
| **Grain** | One row per rating event |
| Natural key | `rating_id` |

---

## Dimension Tables

| Dimension | Type | Notes |
|-----------|------|-------|
| `dim_user` | **SCD Type 2** | `effective_date`, `expiration_date`, `is_current` |
| `dim_driver` | Type 1 | Current-state snapshot |
| `dim_vehicle` | Type 1 | Linked to driver |
| `dim_city` | Type 1 | 10 Pakistani-inspired cities |
| `dim_zone` | Type 1 | ~10 zones per city |
| `dim_date` | Static | 2024-01-01 to 2025-12-31 |
| `dim_time` | Static | Minute-level (0–1439) |
| `dim_payment_method` | Static | Cash, cards, wallet, etc. |
| `dim_ride_status` | Static | Requested through Completed |
| `dim_promotion` | Type 1 | Promo campaigns |

---

## SCD Type 2 — dim_user

`dim_user` supports historical tracking when a user's city, type, or status changes.

| Column | Purpose |
|--------|---------|
| `user_key` | Surrogate key (unique per version) |
| `user_id` | Business key |
| `effective_date` | Version start |
| `expiration_date` | Version end (`9999-12-31` for current) |
| `is_current` | `TRUE` for active version |

**Initial load:** One current row per user.  
**Future incremental loads:** When `updated_at` changes on source, close prior row and insert new version (macro: `dbt/macros/scd_type2.sql`).

Query pattern for current users:

```sql
SELECT * FROM warehouse.dim_user WHERE is_current = TRUE;
```

`fact_rides` joins to `dim_user` on `user_id` filtered to `is_current = TRUE`.

---

## Analytics Layer

Marts in schema `analytics` aggregate facts for BI:

| Mart | Primary grain |
|------|---------------|
| `mart_daily_ride_metrics` | date_key |
| `mart_monthly_ride_metrics` | month |
| `mart_city_performance` | city |
| `mart_zone_performance` | zone |
| `mart_user_activity` | user |
| `mart_driver_performance` | driver |
| `mart_vehicle_performance` | vehicle_type |
| `mart_payment_performance` | payment_method |
| `mart_cancellation_analysis` | multi-dimensional |
| `mart_surge_analysis` | surge bucket |
| `mart_supply_demand` | city × hour |
| `mart_revenue_analysis` | time × city |
| `mart_rating_analysis` | driver / city |
| `mart_cohort_retention` | signup cohort × month |
| `mart_anomaly_monitoring` | anomaly summary |

---

## Raw & Staging Layers

**Raw (`raw.*`):** Landing tables mirroring CSV structure with `source_file`, `ingestion_timestamp`, `batch_id`.

**Staging (`staging.stg_*`):** dbt views that cast types, normalize status capitalization, and handle nulls.

**Intermediate (`staging.int_ride_fare_components`):** Fare decomposition for validation and analytics.

---

## Key Relationships

```text
ride.user_id        → dim_user.user_id
ride.driver_id      → dim_driver.driver_id
ride.vehicle_id     → dim_vehicle.vehicle_id
ride.city_id        → dim_city.city_id
ride.pickup_zone_id → dim_zone.zone_id
payment.ride_id     → fact_rides.ride_id
rating.ride_id      → fact_rides.ride_id
session.driver_id   → dim_driver.driver_id
```

Referential integrity is enforced in validation (pre-load) and dbt tests where applicable.
