"""Load source CSVs into PostgreSQL raw schema with batch metadata."""

from __future__ import annotations

import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import click
import pandas as pd
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings
from src.utils.db import get_engine
from src.utils.logging_config import setup_logging

TABLE_GLOBS = {
    "cities": "**/cities.csv",
    "zones": "**/zones.csv",
    "users": "**/users.csv",
    "drivers": "**/drivers.csv",
    "vehicles": "**/vehicles.csv",
    "rides": "**/rides.csv",
    "driver_sessions": "**/driver_sessions.csv",
    "payments": "**/payments.csv",
    "ratings": "**/ratings.csv",
    "promotions": "**/promotions.csv",
}

# Natural keys used for deduplication / upsert idempotency
NATURAL_KEYS = {
    "cities": ["city_id"],
    "zones": ["zone_id"],
    "users": ["user_id"],
    "drivers": ["driver_id"],
    "vehicles": ["vehicle_id"],
    "rides": ["ride_id"],
    "driver_sessions": ["session_id"],
    "payments": ["payment_id"],
    "ratings": ["rating_id"],
    "promotions": ["promotion_id"],
}


def _find_csv(source_dir: Path, pattern: str) -> Optional[Path]:
    matches = list(source_dir.glob(pattern))
    return matches[0] if matches else None


def _dedupe(df: pd.DataFrame, keys: List[str]) -> pd.DataFrame:
    if not keys or not all(k in df.columns for k in keys):
        return df
    return df.drop_duplicates(subset=keys, keep="last")


def load_table(
    table: str,
    source_dir: Path,
    batch_id: str,
    engine,
    mode: str = "full",
    watermark: Optional[datetime] = None,
) -> int:
    path = _find_csv(source_dir, TABLE_GLOBS[table])
    if path is None:
        return 0

    df = pd.read_csv(path)
    df = _dedupe(df, NATURAL_KEYS[table])

    # Incremental filter when updated_at / event timestamp present
    if mode == "incremental" and watermark is not None:
        ts_col = None
        for candidate in ("updated_at", "request_timestamp", "payment_timestamp", "rating_timestamp", "session_start"):
            if candidate in df.columns:
                ts_col = candidate
                break
        if ts_col:
            df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
            df = df[df[ts_col] > watermark]

    if df.empty:
        return 0

    df["source_file"] = str(path.as_posix())
    df["ingestion_timestamp"] = datetime.utcnow()
    df["batch_id"] = batch_id

    # Truncate + reload for full; for incremental delete overlapping keys then append
    with engine.begin() as conn:
        if mode == "full":
            conn.execute(text(f"TRUNCATE TABLE raw.{table}"))
        else:
            keys = NATURAL_KEYS[table]
            key = keys[0]
            ids = tuple(df[key].dropna().unique().tolist())
            if ids:
                # chunk deletes for large sets
                chunk = 5000
                for i in range(0, len(ids), chunk):
                    subset = ids[i : i + chunk]
                    conn.execute(
                        text(f"DELETE FROM raw.{table} WHERE {key} = ANY(:ids)"),
                        {"ids": list(subset)},
                    )
        df.to_sql(table, conn, schema="raw", if_exists="append", index=False, method="multi", chunksize=2000)

    return len(df)


def update_watermark(engine, pipeline_name: str, table_name: str, watermark: datetime, batch_id: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO audit.pipeline_watermarks (pipeline_name, table_name, watermark_ts, batch_id, updated_at)
                VALUES (:pipeline, :table, :wm, :batch, NOW())
                ON CONFLICT (pipeline_name, table_name)
                DO UPDATE SET watermark_ts = EXCLUDED.watermark_ts,
                              batch_id = EXCLUDED.batch_id,
                              updated_at = NOW()
                """
            ),
            {"pipeline": pipeline_name, "table": table_name, "wm": watermark, "batch": batch_id},
        )


def get_watermark(engine, pipeline_name: str, table_name: str) -> Optional[datetime]:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT watermark_ts FROM audit.pipeline_watermarks
                WHERE pipeline_name = :p AND table_name = :t
                """
            ),
            {"p": pipeline_name, "t": table_name},
        ).fetchone()
        return row[0] if row else None


def start_pipeline_run(engine, pipeline_name: str, batch_id: str) -> str:
    run_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO audit.pipeline_runs
                    (run_id, pipeline_name, start_time, status, batch_id)
                VALUES (:run_id, :name, NOW(), 'Running', :batch)
                """
            ),
            {"run_id": run_id, "name": pipeline_name, "batch": batch_id},
        )
    return run_id


def finish_pipeline_run(
    engine,
    run_id: str,
    status: str,
    records_processed: int = 0,
    records_failed: int = 0,
    error_message: Optional[str] = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE audit.pipeline_runs
                SET end_time = NOW(),
                    status = :status,
                    records_processed = :proc,
                    records_failed = :fail,
                    error_message = :err
                WHERE run_id = :run_id
                """
            ),
            {
                "run_id": run_id,
                "status": status,
                "proc": records_processed,
                "fail": records_failed,
                "err": error_message,
            },
        )


def ingest_all(mode: str = "full", source_dir: Optional[Path] = None) -> Dict[str, int]:
    settings = get_settings()
    log = setup_logging()
    engine = get_engine()
    source = source_dir or settings.source_dir
    batch_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    run_id = start_pipeline_run(engine, "raw_ingestion", batch_id)
    counts: Dict[str, int] = {}
    total = 0
    try:
        for table in TABLE_GLOBS:
            wm = get_watermark(engine, "raw_ingestion", table) if mode == "incremental" else None
            n = load_table(table, source, batch_id, engine, mode=mode, watermark=wm)
            counts[table] = n
            total += n
            log.info("Loaded raw.%s: %s rows (mode=%s)", table, n, mode)
            if n > 0:
                update_watermark(engine, "raw_ingestion", table, datetime.utcnow(), batch_id)
        finish_pipeline_run(engine, run_id, "Success", records_processed=total)
    except Exception as exc:
        finish_pipeline_run(engine, run_id, "Failure", records_processed=total, error_message=str(exc))
        raise
    return counts


@click.command()
@click.option("--mode", type=click.Choice(["full", "incremental"]), default="full")
@click.option("--source-dir", type=click.Path(exists=True, path_type=Path), default=None)
def main(mode: str, source_dir: Path | None) -> None:
    counts = ingest_all(mode=mode, source_dir=source_dir)
    for k, v in counts.items():
        click.echo(f"{k}: {v}")


if __name__ == "__main__":
    main()
