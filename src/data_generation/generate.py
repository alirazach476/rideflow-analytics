"""CLI entrypoint: generate synthetic RideFlow source CSVs."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

import click
import pandas as pd
from tqdm import tqdm

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings
from src.data_generation.dq_issues import inject_quality_issues
from src.data_generation.generators import RideFlowGenerator
from src.utils.logging_config import setup_logging

SOURCE_MAP = {
    "cities": "ride_platform",
    "zones": "ride_platform",
    "users": "user_platform",
    "drivers": "driver_platform",
    "vehicles": "driver_platform",
    "rides": "ride_platform",
    "driver_sessions": "driver_platform",
    "payments": "payment_platform",
    "ratings": "rating_platform",
    "promotions": "promotion_platform",
}


def _write_csv(rows: List[Dict[str, Any]], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return len(df)


def generate_all(sample: bool = False) -> Dict[str, int]:
    settings = get_settings()
    log = setup_logging()
    gen = RideFlowGenerator(seed=settings.random_seed)

    if sample:
        n_users, n_drivers, n_vehicles = 500, 100, 110
        n_rides, n_sessions, n_promos = 2000, 500, 10
        n_cities, n_zones = 10, 50
        out_root = settings.resolve_path("data/samples")
    else:
        n_users = settings.num_users
        n_drivers = settings.num_drivers
        n_vehicles = settings.num_vehicles
        n_rides = settings.num_rides
        n_sessions = settings.num_driver_sessions
        n_promos = settings.num_promotions
        n_cities = settings.num_cities
        n_zones = settings.num_zones
        out_root = settings.source_dir

    start = date.fromisoformat(settings.data_start_date)
    end = date.fromisoformat(settings.data_end_date)

    log.info("Generating cities/zones...")
    cities = gen.generate_cities(n_cities)
    zones = gen.generate_zones(cities, n_zones)

    log.info("Generating users (%s)...", n_users)
    users = gen.generate_users(n_users, cities, start, end)

    log.info("Generating drivers (%s)...", n_drivers)
    drivers = gen.generate_drivers(n_drivers, cities, start, end)

    log.info("Generating vehicles (%s)...", n_vehicles)
    vehicles = gen.generate_vehicles(n_vehicles, drivers)

    log.info("Generating promotions (%s)...", n_promos)
    promotions = gen.generate_promotions(n_promos, start, end)

    log.info("Generating rides/payments/ratings (%s rides)...", n_rides)
    rides, payments, ratings = gen.generate_rides(
        n_rides, users, drivers, vehicles, zones, promotions, start, end
    )

    log.info("Generating driver sessions (%s)...", n_sessions)
    sessions = gen.generate_driver_sessions(n_sessions, drivers, zones, start, end)

    datasets = {
        "cities": cities,
        "zones": zones,
        "users": users,
        "drivers": drivers,
        "vehicles": vehicles,
        "rides": rides,
        "driver_sessions": sessions,
        "payments": payments,
        "ratings": ratings,
        "promotions": promotions,
    }

    log.info("Injecting intentional DQ issues (rate=%s)...", settings.dq_issue_rate)
    datasets = inject_quality_issues(datasets, rate=settings.dq_issue_rate, seed=settings.random_seed)

    counts: Dict[str, int] = {}
    for name, rows in tqdm(datasets.items(), desc="Writing CSVs"):
        platform = SOURCE_MAP[name]
        path = out_root / platform / f"{name}.csv"
        counts[name] = _write_csv(rows, path)
        log.info("Wrote %s (%s rows)", path, counts[name])

    # Also copy sample snapshot metadata
    meta = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sample": sample,
        "counts": counts,
        "seed": settings.random_seed,
        "date_range": [settings.data_start_date, settings.data_end_date],
    }
    meta_path = out_root / "generation_manifest.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    log.info("Manifest written to %s", meta_path)
    return counts


@click.command()
@click.option("--sample", is_flag=True, help="Generate a small sample dataset for quick tests.")
def main(sample: bool) -> None:
    counts = generate_all(sample=sample)
    click.echo("Generation complete:")
    for k, v in counts.items():
        click.echo(f"  {k}: {v:,}")


if __name__ == "__main__":
    main()
