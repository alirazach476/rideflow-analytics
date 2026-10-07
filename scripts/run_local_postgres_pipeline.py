"""
Run RideFlow ETL against a local pgserver-backed PostgreSQL instance
when Docker is unavailable. Same schemas / dbt / Python modules as Docker flow.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ["PYTHONPATH"] = str(ROOT)


def apply_ddl(engine) -> None:
    for rel in [
        "sql/ddl/01_schemas.sql",
        "sql/ddl/02_raw_tables.sql",
        "sql/ddl/03_audit_monitoring.sql",
    ]:
        sql = (ROOT / rel).read_text(encoding="utf-8")
        statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("\\")]
        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(text(stmt))
        print(f"Applied {rel}")


def main() -> None:
    from pgserver import get_server

    from src.data_generation.generate import generate_all

    if not list((ROOT / "data" / "samples").glob("**/rides.csv")):
        print("Generating sample data...")
        generate_all(sample=True)

    src = ROOT / "data" / "samples"
    dst = ROOT / "data" / "source"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("generation_manifest.json"))
    print("Source data ready at data/source")

    pgdata = ROOT / ".pgdata"
    pgdata.mkdir(exist_ok=True)
    print("Starting pgserver PostgreSQL...")
    # Keep server running after script so follow-up queries / Power BI can connect.
    server = get_server(pgdata, cleanup_mode=None)
    url = server.get_uri()
    print("Postgres URI:", url)

    parsed = urlparse(url)
    os.environ["POSTGRES_HOST"] = parsed.hostname or "127.0.0.1"
    os.environ["POSTGRES_PORT"] = str(parsed.port)
    os.environ["POSTGRES_USER"] = parsed.username or "postgres"
    os.environ["POSTGRES_PASSWORD"] = parsed.password or ""
    os.environ["POSTGRES_DB"] = (parsed.path or "/postgres").lstrip("/") or "postgres"

    from config.settings import get_settings

    get_settings.cache_clear()

    sa_url = url.replace("postgresql://", "postgresql+psycopg2://")
    # Handle postgresql://user@host without password
    if parsed.password is None and "@" in sa_url:
        # psycopg2 may need empty password explicitly
        pass
    engine = create_engine(sa_url, pool_pre_ping=True)
    apply_ddl(engine)

    from src.ingestion.load_raw import ingest_all
    from src.validation.checks import run_validation

    print("Validating...")
    summary = run_validation(data_dir=ROOT / "data" / "source")["summary"]
    print("DQ:", summary)

    print("Ingesting raw (full)...")
    counts = ingest_all(mode="full", source_dir=ROOT / "data" / "source")
    print(counts)

    print("Re-ingesting (idempotency check)...")
    ingest_all(mode="full", source_dir=ROOT / "data" / "source")
    with engine.connect() as conn:
        ride_n = conn.execute(text("SELECT COUNT(*) FROM raw.rides")).scalar()
        distinct_n = conn.execute(text("SELECT COUNT(DISTINCT ride_id) FROM raw.rides")).scalar()
    print(f"raw.rides rows={ride_n}, distinct ride_id={distinct_n}")
    assert ride_n == distinct_n, "Idempotent full load should not leave duplicates"

    (ROOT / "dbt" / "profiles.yml").write_text(
        f"""rideflow:
  target: dev
  outputs:
    dev:
      type: postgres
      host: "{os.environ['POSTGRES_HOST']}"
      port: {os.environ['POSTGRES_PORT']}
      user: "{os.environ['POSTGRES_USER']}"
      password: "{os.environ.get('POSTGRES_PASSWORD') or ''}"
      dbname: "{os.environ['POSTGRES_DB']}"
      schema: staging
      threads: 2
""",
        encoding="utf-8",
    )

    env = os.environ.copy()
    print("Running dbt run...")
    result = subprocess.run(
        ["dbt", "run", "--profiles-dir", "."],
        cwd=str(ROOT / "dbt"),
        env=env,
        capture_output=True,
        text=True,
    )
    print(result.stdout[-5000:] if result.stdout else "")
    if result.returncode != 0:
        print(result.stderr[-5000:] if result.stderr else "")
        raise SystemExit(f"dbt run failed: {result.returncode}")

    # Apply warehouse indexes (best effort)
    idx_sql = (ROOT / "sql" / "performance" / "indexes.sql").read_text(encoding="utf-8")
    with engine.begin() as conn:
        for stmt in [s.strip() for s in idx_sql.split(";") if s.strip()]:
            try:
                conn.execute(text(stmt))
            except Exception as exc:
                print("Index note:", exc)

    from src.anomaly_detection.detect import run_anomaly_detection
    from src.transformation.reconcile import run_reconciliation

    print("Reconciliation...")
    reco = run_reconciliation()
    for r in reco:
        print(r)

    print("Anomaly detection...")
    anom = run_anomaly_detection()
    print(anom)

    # Rebuild anomaly mart after anomalies populated
    subprocess.run(
        ["dbt", "run", "--select", "mart_anomaly_monitoring", "--profiles-dir", "."],
        cwd=str(ROOT / "dbt"),
        env=env,
        check=False,
    )

    print("Generating insights...")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_insights.py")], env=env, check=False)

    status = ROOT / "data" / "processed" / "local_pipeline_status.txt"
    status.write_text(
        f"PASS\nrides={counts.get('rides')}\nraw_rides={ride_n}\nanomalies={anom}\nreco={reco}\n",
        encoding="utf-8",
    )
    print("LOCAL PIPELINE COMPLETE ->", status)


if __name__ == "__main__":
    main()
