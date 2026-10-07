-- Audit & monitoring tables

CREATE TABLE IF NOT EXISTS audit.pipeline_runs (
    run_id              TEXT PRIMARY KEY,
    pipeline_name       TEXT NOT NULL,
    start_time          TIMESTAMP NOT NULL,
    end_time            TIMESTAMP,
    status              TEXT NOT NULL,
    records_processed   INTEGER DEFAULT 0,
    records_failed      INTEGER DEFAULT 0,
    error_message       TEXT,
    batch_id            TEXT
);

CREATE TABLE IF NOT EXISTS audit.pipeline_watermarks (
    pipeline_name       TEXT NOT NULL,
    table_name          TEXT NOT NULL,
    watermark_ts        TIMESTAMP NOT NULL,
    batch_id            TEXT,
    updated_at          TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (pipeline_name, table_name)
);

CREATE TABLE IF NOT EXISTS audit.reconciliation_results (
    reconciliation_id   SERIAL PRIMARY KEY,
    run_id              TEXT NOT NULL,
    metric_name         TEXT NOT NULL,
    source_value        DOUBLE PRECISION,
    warehouse_value     DOUBLE PRECISION,
    difference          DOUBLE PRECISION,
    status              TEXT NOT NULL CHECK (status IN ('PASS', 'WARNING', 'FAIL')),
    checked_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit.data_quality_results (
    check_id            SERIAL PRIMARY KEY,
    run_id              TEXT,
    check_name          TEXT NOT NULL,
    table_name          TEXT,
    status              TEXT NOT NULL,
    expected_value      TEXT,
    actual_value        TEXT,
    message             TEXT,
    checked_at          TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS monitoring.ride_anomalies (
    anomaly_id          SERIAL PRIMARY KEY,
    ride_id             INTEGER NOT NULL,
    user_id             INTEGER,
    driver_id           INTEGER,
    timestamp           TIMESTAMP,
    fare                DOUBLE PRECISION,
    rule_based_score    DOUBLE PRECISION,
    ml_anomaly_score    DOUBLE PRECISION,
    anomaly_reason      TEXT,
    severity            TEXT CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    detected_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anomalies_ride ON monitoring.ride_anomalies (ride_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_severity ON monitoring.ride_anomalies (severity);
CREATE INDEX IF NOT EXISTS idx_anomalies_detected ON monitoring.ride_anomalies (detected_at);
