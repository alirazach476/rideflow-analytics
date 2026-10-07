"""Central configuration for RideFlow Analytics Platform."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "rideflow"
    postgres_user: str = "rideflow"
    postgres_password: str = "rideflow_secret"

    # Dataset sizes
    num_users: int = 10_000
    num_drivers: int = 2_000
    num_vehicles: int = 2_200
    num_cities: int = 10
    num_zones: int = 100
    num_rides: int = 100_000
    num_driver_sessions: int = 50_000
    num_promotions: int = 50

    # Generation
    random_seed: int = 42
    data_start_date: str = "2024-01-01"
    data_end_date: str = "2025-12-31"
    dq_issue_rate: float = 0.002

    # Anomaly
    anomaly_zscore_threshold: float = 3.0
    anomaly_isolation_forest: bool = True

    # Paths
    data_source_dir: str = "data/source"
    data_raw_dir: str = "data/raw"
    data_processed_dir: str = "data/processed"

    # Pipeline
    batch_size: int = 10_000
    fare_tolerance: float = 0.05

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def psycopg2_dsn(self) -> str:
        return (
            f"host={self.postgres_host} port={self.postgres_port} "
            f"dbname={self.postgres_db} user={self.postgres_user} "
            f"password={self.postgres_password}"
        )

    def resolve_path(self, relative: str) -> Path:
        path = Path(relative)
        if path.is_absolute():
            return path
        return PROJECT_ROOT / path

    @property
    def source_dir(self) -> Path:
        return self.resolve_path(self.data_source_dir)

    @property
    def raw_dir(self) -> Path:
        return self.resolve_path(self.data_raw_dir)

    @property
    def processed_dir(self) -> Path:
        return self.resolve_path(self.data_processed_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
