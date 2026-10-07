"""
SCD Type 2 updates for warehouse.dim_user.

When a user's city_id, user_type, or status changes:
  1. Expire the current row (set expiration_date, is_current=false)
  2. Insert a new current version with a new user_key
"""

from __future__ import annotations

import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import click
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.utils.db import get_engine
from src.utils.logging_config import setup_logging

TRACKED = ("city_id", "user_type", "status")


def _key(user_id: int, effective: datetime) -> str:
    raw = f"{user_id}|{effective.isoformat()}"
    return hashlib.md5(raw.encode()).hexdigest()


def apply_user_changes(changes: List[Dict[str, Any]]) -> int:
    """
    Apply SCD2 changes.
    Each change dict: {user_id, city_id?, user_type?, status?, effective_date?}
    """
    log = setup_logging()
    engine = get_engine()
    applied = 0
    with engine.begin() as conn:
        for ch in changes:
            user_id = int(ch["user_id"])
            current = conn.execute(
                text(
                    """
                    SELECT user_key, city_id, user_type, status
                    FROM warehouse.dim_user
                    WHERE user_id = :uid AND is_current = TRUE
                    """
                ),
                {"uid": user_id},
            ).mappings().fetchone()
            if not current:
                log.warning("No current dim_user row for user_id=%s", user_id)
                continue

            new_vals = {k: ch.get(k, current[k]) for k in TRACKED}
            if all(new_vals[k] == current[k] for k in TRACKED):
                continue

            effective = ch.get("effective_date") or datetime.utcnow()
            conn.execute(
                text(
                    """
                    UPDATE warehouse.dim_user
                    SET is_current = FALSE,
                        expiration_date = :eff
                    WHERE user_id = :uid AND is_current = TRUE
                    """
                ),
                {"uid": user_id, "eff": effective},
            )
            row = conn.execute(
                text(
                    """
                    SELECT first_name, last_name, gender, date_of_birth,
                           registration_date, signup_channel, updated_at
                    FROM warehouse.dim_user
                    WHERE user_key = :uk
                    """
                ),
                {"uk": current["user_key"]},
            ).mappings().fetchone()
            conn.execute(
                text(
                    """
                    INSERT INTO warehouse.dim_user (
                        user_key, user_id, first_name, last_name, gender, date_of_birth,
                        registration_date, city_id, user_type, status, signup_channel,
                        effective_date, expiration_date, is_current, updated_at
                    ) VALUES (
                        :user_key, :user_id, :first_name, :last_name, :gender, :date_of_birth,
                        :registration_date, :city_id, :user_type, :status, :signup_channel,
                        :effective_date, TIMESTAMP '9999-12-31', TRUE, :updated_at
                    )
                    """
                ),
                {
                    "user_key": _key(user_id, effective),
                    "user_id": user_id,
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "gender": row["gender"],
                    "date_of_birth": row["date_of_birth"],
                    "registration_date": row["registration_date"],
                    "city_id": new_vals["city_id"],
                    "user_type": new_vals["user_type"],
                    "status": new_vals["status"],
                    "signup_channel": row["signup_channel"],
                    "effective_date": effective,
                    "updated_at": effective,
                },
            )
            applied += 1
            log.info("SCD2 applied for user_id=%s", user_id)
    return applied


@click.command()
@click.option("--user-id", type=int, required=True)
@click.option("--city-id", type=int, default=None)
@click.option("--user-type", type=str, default=None)
@click.option("--status", type=str, default=None)
def main(user_id: int, city_id: int | None, user_type: str | None, status: str | None) -> None:
    change: Dict[str, Any] = {"user_id": user_id}
    if city_id is not None:
        change["city_id"] = city_id
    if user_type is not None:
        change["user_type"] = user_type
    if status is not None:
        change["status"] = status
    n = apply_user_changes([change])
    click.echo(f"Applied {n} SCD2 change(s)")


if __name__ == "__main__":
    main()
