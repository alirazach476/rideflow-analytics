"""CLI: run data quality validation."""

from __future__ import annotations

import sys
from pathlib import Path

import click

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging_config import setup_logging
from src.validation.checks import run_validation


@click.command()
@click.option("--data-dir", type=click.Path(exists=True, path_type=Path), default=None)
def main(data_dir: Path | None) -> None:
    log = setup_logging()
    report = run_validation(data_dir=data_dir)
    summary = report["summary"]
    log.info("DQ Summary: %s", summary)
    log.info("Results saved to %s", report["output"])
    # Intentionally injected issues should cause FAILs — exit 0 so pipeline can quarantine
    click.echo(summary)


if __name__ == "__main__":
    main()
