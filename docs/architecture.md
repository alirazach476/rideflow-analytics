# RideFlow Architecture

This document describes the **local batch architecture** of the RideFlow Analytics Platform. All processing runs on a developer machine via Python, PostgreSQL (Docker), dbt, and Airflow — not in a cloud environment.

---

## Overall Architecture

```mermaid
flowchart LR
    subgraph Gen["Data Generation"]
        PY[Python + Faker]
        CSV[CSV Exports]
    end

    subgraph Ingest["Ingestion Layer"]
        VAL[Validation Framework]
        LOAD[load_raw.py]
    end

    subgraph PG["PostgreSQL"]
        RAW[(raw)]
        STG[(staging)]
        WH[(warehouse)]
        AN[(analytics)]
        AUD[(audit)]
        MON[(monitoring)]
    end

    subgraph Transform["Transformation"]
        DBT[dbt Core]
    end

    subgraph Ops["Operations"]
        AF[Airflow DAG]
        REC[Reconciliation]
        AD[Anomaly Screening]
    end

    subgraph BI["BI"]
        PBI[Power BI Desktop]
    end

    PY --> CSV --> VAL --> LOAD --> RAW
    RAW --> DBT --> STG --> WH --> AN
    DBT --> AN
    AF --> Gen
    AF --> Ingest
    AF --> Transform
    AF --> REC
    AF --> AD
    WH --> PBI
    AN --> PBI
    MON --> PBI
    AUD --> PBI
```

---

## ETL Pipeline

RideFlow uses an **ELT** pattern: load raw data first, transform in-database with dbt.

```mermaid
flowchart TD
    A[Generate CSVs<br/>data/source/] --> B{Validation}
    B -->|PASS/WARNING| C[Ingest to raw.*]
    B -->|FAIL| X[Review dq_results.json]
    C --> D[dbt staging views<br/>cleansing & typing]
    D --> E[dbt intermediate<br/>fare components]
    E --> F[dbt warehouse<br/>dimensions & facts]
    F --> G[dbt analytics marts]
    G --> H[Reconciliation]
    G --> I[Anomaly Screening]
    H --> J[Audit Tables]
    I --> J
    G --> K[SQL Analytics / Power BI]
```

**Batch boundaries:** Each run receives a unique `batch_id`. Full mode truncates raw tables; incremental mode filters by watermark timestamps and upserts by natural key.

---

## Database Architecture

```mermaid
flowchart TB
    subgraph Schemas
        RAW[raw<br/>Landing zone — permissive types]
        STG[staging<br/>dbt views — cleaned]
        WH[warehouse<br/>Star schema tables]
        AN[analytics<br/>Business marts]
        AUD[audit<br/>Runs, watermarks, reconciliation]
        MON[monitoring<br/>Anomaly screening results]
    end

    RAW --> STG --> WH --> AN
    WH --> MON
    AUD -. tracks .-> RAW
    AUD -. tracks .-> WH
```

| Schema | Purpose |
|--------|---------|
| `raw` | CSV landing with ingestion metadata |
| `staging` | Typed, standardized views |
| `warehouse` | Conformed dimensions + facts |
| `analytics` | Aggregated marts for BI |
| `audit` | Pipeline runs, watermarks, reconciliation |
| `monitoring` | Potential anomaly flags |

DDL: `sql/ddl/01_schemas.sql`, `02_raw_tables.sql`, `03_audit_monitoring.sql`

---

## Star Schema

```mermaid
erDiagram
    fact_rides ||--o{ dim_date : date_key
    fact_rides ||--o{ dim_time : time_key
    fact_rides ||--o{ dim_user : user_key
    fact_rides ||--o{ dim_driver : driver_key
    fact_rides ||--o{ dim_vehicle : vehicle_key
    fact_rides ||--o{ dim_city : city_key
    fact_rides ||--o{ dim_zone : pickup_zone_key
    fact_rides ||--o{ dim_zone : dropoff_zone_key
    fact_rides ||--o{ dim_ride_status : status_key

    fact_payments ||--o{ dim_date : date_key
    fact_payments ||--o{ dim_payment_method : payment_method_key

    fact_driver_sessions ||--o{ dim_driver : driver_key
    fact_driver_sessions ||--o{ dim_city : city_key
    fact_driver_sessions ||--o{ dim_zone : zone_key

    fact_ratings ||--o{ dim_user : user_key
    fact_ratings ||--o{ dim_driver : driver_key

    fact_rides {
        text ride_key PK
        int ride_id
        int date_key FK
        int time_key FK
        boolean is_completed
        boolean is_cancelled
        numeric total_fare
    }

    dim_user {
        text user_key PK
        int user_id
        boolean is_current
        timestamp effective_date
        timestamp expiration_date
    }
```

**Fact grain:** `fact_rides` = one row per ride request/event.

---

## Airflow DAG

DAG ID: `rideflow_daily_pipeline`  
Schedule: `@daily` (batch, not streaming)

```mermaid
flowchart TD
    start([start]) --> check_sources[check_sources]
    check_sources --> generate[generate_or_receive_data]
    generate --> iu[ingest_users]
    generate --> id[ingest_drivers]
    generate --> iv[ingest_vehicles]
    generate --> ir[ingest_rides]
    generate --> ip[ingest_payments]
    generate --> irt[ingest_ratings]
    iu & id & iv & ir & ip & irt --> validate[validate_data]
    validate --> load_raw[load_raw]
    load_raw --> dbt_stg[dbt_staging]
    dbt_stg --> dbt_wh[dbt_warehouse]
    dbt_wh --> dbt_an[dbt_analytics]
    dbt_an --> recon[reconciliation]
    recon --> anomaly[anomaly_detection]
    anomaly --> dq_test[data_quality_tests]
    dq_test --> audit[update_audit]
    audit --> end([end])
```

Per-entity ingest tasks are placeholders; actual loading occurs in `load_raw`. Retries: 2, delay: 3 minutes.

---

## Data Quality Flow

```mermaid
flowchart LR
    CSV[Source CSVs] --> PRE[Pre-load Validation<br/>src/validation/checks.py]
    PRE --> JSON[dq_results.json]
    PRE --> ING[Ingestion]
    ING --> RAW[raw tables]
    RAW --> DBT[dbt staging tests<br/>not_null, unique]
    DBT --> WH[Warehouse]
    WH --> REC[Reconciliation<br/>counts & revenue]
    REC --> AUD[audit.reconciliation_results]
```

Validation runs **before** ingestion in the Makefile pipeline. Intentional source issues are injected at ~0.2% rate for realism.

---

## Anomaly Detection Flow

```mermaid
flowchart TD
    FR[warehouse.fact_rides<br/>completed rides] --> RB[Rule-Based Flags]
    FR --> ZS[Z-Score Screening<br/>per customer]
    FR --> IF[Isolation Forest<br/>optional]
    RB --> MERGE[Merge & dedupe<br/>by ride_id]
    ZS --> MERGE
    IF --> MERGE
    MERGE --> MA[monitoring.ride_anomalies]
    MA --> MART[analytics.mart_anomaly_monitoring]
    MA --> PBI[Power BI Anomaly Page]
```

**Important:** Outputs are labeled *potential anomalies* for operational review — not fraud determinations.

---

## Deployment Topology (Local)

```text
Host Machine
├── Python venv (generation, ingestion, validation, anomaly, reconcile)
├── Docker Compose
│   ├── postgres:5432 (rideflow DB + airflow DB)
│   ├── airflow-webserver:8080
│   └── airflow-scheduler
└── Power BI Desktop → connects to localhost:5432
```

No Kubernetes, no managed cloud warehouse in the default setup.
