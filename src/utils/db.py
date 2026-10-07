"""Database connection helpers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Iterator

import psycopg2
from psycopg2.extensions import connection as PgConnection
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config.settings import get_settings


def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


@contextmanager
def get_connection() -> Iterator[PgConnection]:
    settings = get_settings()
    conn = psycopg2.connect(settings.psycopg2_dsn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def test_connection() -> bool:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        return result == 1
