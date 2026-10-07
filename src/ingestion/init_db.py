"""Initialize PostgreSQL schemas and raw/audit/monitoring tables."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.db import get_engine, test_connection
from src.utils.logging_config import setup_logging

DDL_FILES = [
    "sql/ddl/01_schemas.sql",
    "sql/ddl/02_raw_tables.sql",
    "sql/ddl/03_audit_monitoring.sql",
]


def init_database() -> None:
    log = setup_logging()
    if not test_connection():
        raise RuntimeError("Cannot connect to PostgreSQL")
    engine = get_engine()
    with engine.begin() as conn:
        for rel in DDL_FILES:
            path = PROJECT_ROOT / rel
            sql = path.read_text(encoding="utf-8")
            # Strip psql meta-commands if present
            statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("\\")]
            for stmt in statements:
                conn.execute(text(stmt))
            log.info("Applied %s", rel)
    log.info("Database initialized successfully")


@click.command()
def main() -> None:
    init_database()


if __name__ == "__main__":
    main()
