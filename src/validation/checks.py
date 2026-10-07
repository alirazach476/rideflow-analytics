"""Automated data-quality checks for RideFlow source / raw data."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd

from config.pricing import TAX_RATE, VEHICLE_PRICING, calculate_fare
from config.settings import get_settings


@dataclass
class CheckResult:
    check_name: str
    table_name: str
    status: str  # PASS | WARNING | FAIL
    expected: Any
    actual: Any
    message: str
    checked_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class DataQualityFramework:
    """Run null, uniqueness, referential, numeric, timestamp, and fare checks."""

    VALID_RIDE_STATUSES = {
        "Requested",
        "Accepted",
        "Driver_Cancelled",
        "Rider_Cancelled",
        "Completed",
        "No_Driver_Available",
    }
    VALID_PAYMENT_STATUSES = {"Completed", "Failed", "Refunded", "Pending"}

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        settings = get_settings()
        self.data_dir = data_dir or settings.source_dir
        self.fare_tolerance = settings.fare_tolerance
        self.results: List[CheckResult] = []
        self.tables: Dict[str, pd.DataFrame] = {}

    def load_tables(self) -> None:
        mapping = {
            "users": "**/users.csv",
            "drivers": "**/drivers.csv",
            "vehicles": "**/vehicles.csv",
            "rides": "**/rides.csv",
            "payments": "**/payments.csv",
            "ratings": "**/ratings.csv",
            "cities": "**/cities.csv",
            "zones": "**/zones.csv",
            "driver_sessions": "**/driver_sessions.csv",
            "promotions": "**/promotions.csv",
        }
        for name, pattern in mapping.items():
            matches = list(self.data_dir.glob(pattern))
            if matches:
                self.tables[name] = pd.read_csv(matches[0])

    def run_all(self) -> List[CheckResult]:
        self.load_tables()
        self._null_checks()
        self._uniqueness_checks()
        self._referential_checks()
        self._numeric_checks()
        self._timestamp_checks()
        self._fare_reconciliation()
        self._status_checks()
        return self.results

    def summary(self) -> Dict[str, int]:
        counts = {"PASS": 0, "WARNING": 0, "FAIL": 0}
        for r in self.results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return counts

    def save_results(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(r) for r in self.results]
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    def _add(self, **kwargs: Any) -> None:
        self.results.append(CheckResult(**kwargs))

    def _null_checks(self) -> None:
        required = {
            "users": ["user_id", "registration_date", "city_id", "user_type", "status"],
            "drivers": ["driver_id", "registration_date", "city_id", "status", "rating"],
            "vehicles": ["vehicle_id", "driver_id", "vehicle_type", "status"],
            "rides": ["ride_id", "user_id", "city_id", "request_timestamp", "ride_status"],
            "payments": ["payment_id", "ride_id", "user_id", "amount", "payment_status"],
        }
        for table, cols in required.items():
            if table not in self.tables:
                continue
            df = self.tables[table]
            for col in cols:
                if col not in df.columns:
                    self._add(
                        check_name="null_check",
                        table_name=table,
                        status="FAIL",
                        expected="column exists",
                        actual="missing",
                        message=f"Column {col} missing from {table}",
                    )
                    continue
                nulls = int(df[col].isna().sum())
                self._add(
                    check_name=f"null_{col}",
                    table_name=table,
                    status="PASS" if nulls == 0 else "FAIL",
                    expected=0,
                    actual=nulls,
                    message=f"{nulls} nulls in {table}.{col}",
                )

    def _uniqueness_checks(self) -> None:
        keys = {
            "users": "user_id",
            "drivers": "driver_id",
            "vehicles": "vehicle_id",
            "rides": "ride_id",
            "payments": "payment_id",
        }
        for table, key in keys.items():
            if table not in self.tables:
                continue
            df = self.tables[table]
            dupes = int(df[key].duplicated().sum())
            self._add(
                check_name=f"unique_{key}",
                table_name=table,
                status="PASS" if dupes == 0 else "FAIL",
                expected=0,
                actual=dupes,
                message=f"{dupes} duplicate {key} values in {table}",
            )

    def _referential_checks(self) -> None:
        if "rides" not in self.tables:
            return
        rides = self.tables["rides"]
        if "users" in self.tables:
            valid: Set[Any] = set(self.tables["users"]["user_id"].dropna().unique())
            bad = int((~rides["user_id"].isin(valid)).sum())
            self._add(
                check_name="fk_ride_user",
                table_name="rides",
                status="PASS" if bad == 0 else "FAIL",
                expected=0,
                actual=bad,
                message=f"{bad} rides with invalid user_id",
            )
        if "drivers" in self.tables:
            valid = set(self.tables["drivers"]["driver_id"].dropna().unique())
            # Null driver_id allowed for Requested / No_Driver_Available
            mask = rides["driver_id"].notna() & ~rides["driver_id"].isin(valid)
            bad = int(mask.sum())
            self._add(
                check_name="fk_ride_driver",
                table_name="rides",
                status="PASS" if bad == 0 else "FAIL",
                expected=0,
                actual=bad,
                message=f"{bad} rides with invalid driver_id",
            )
        if "vehicles" in self.tables:
            valid = set(self.tables["vehicles"]["vehicle_id"].dropna().unique())
            mask = rides["vehicle_id"].notna() & ~rides["vehicle_id"].isin(valid)
            bad = int(mask.sum())
            self._add(
                check_name="fk_ride_vehicle",
                table_name="rides",
                status="PASS" if bad == 0 else "FAIL",
                expected=0,
                actual=bad,
                message=f"{bad} rides with invalid vehicle_id",
            )

    def _numeric_checks(self) -> None:
        if "rides" not in self.tables:
            return
        rides = self.tables["rides"]
        completed = rides[rides["ride_status"].astype(str).str.lower() == "completed"]
        if "distance_km" in completed.columns:
            bad = int(((completed["distance_km"].fillna(0) <= 0)).sum())
            self._add(
                check_name="distance_positive",
                table_name="rides",
                status="PASS" if bad == 0 else "FAIL",
                expected=0,
                actual=bad,
                message=f"{bad} completed rides with distance_km <= 0",
            )
        if "duration_minutes" in completed.columns:
            bad = int(((completed["duration_minutes"].fillna(0) <= 0)).sum())
            self._add(
                check_name="duration_positive",
                table_name="rides",
                status="PASS" if bad == 0 else "FAIL",
                expected=0,
                actual=bad,
                message=f"{bad} completed rides with duration_minutes <= 0",
            )
        if "total_fare" in completed.columns:
            bad = int(((completed["total_fare"].fillna(-1) < 0)).sum())
            self._add(
                check_name="fare_non_negative",
                table_name="rides",
                status="PASS" if bad == 0 else "FAIL",
                expected=0,
                actual=bad,
                message=f"{bad} rides with negative total_fare",
            )
        if "surge_multiplier" in rides.columns:
            bad = int(((rides["surge_multiplier"].fillna(0) < 1)).sum())
            self._add(
                check_name="surge_gte_1",
                table_name="rides",
                status="PASS" if bad == 0 else "FAIL",
                expected=0,
                actual=bad,
                message=f"{bad} rides with surge_multiplier < 1",
            )
        if "ratings" in self.tables:
            r = self.tables["ratings"]
            bad = int(((r["rating"] < 1) | (r["rating"] > 5)).sum())
            self._add(
                check_name="rating_range",
                table_name="ratings",
                status="PASS" if bad == 0 else "FAIL",
                expected=0,
                actual=bad,
                message=f"{bad} ratings outside 1-5",
            )

    def _timestamp_checks(self) -> None:
        if "rides" not in self.tables:
            return
        rides = self.tables["rides"].copy()
        for col in ["request_timestamp", "accepted_timestamp", "pickup_timestamp", "dropoff_timestamp"]:
            if col in rides.columns:
                rides[col] = pd.to_datetime(rides[col], errors="coerce")
        bad = 0
        completed = rides[rides["ride_status"].astype(str).str.lower() == "completed"]
        for _, row in completed.iterrows():
            seq = [row.get("request_timestamp"), row.get("accepted_timestamp"), row.get("pickup_timestamp"), row.get("dropoff_timestamp")]
            seq = [s for s in seq if pd.notna(s)]
            if seq != sorted(seq):
                bad += 1
        self._add(
            check_name="timestamp_sequence",
            table_name="rides",
            status="PASS" if bad == 0 else "FAIL",
            expected=0,
            actual=bad,
            message=f"{bad} completed rides with invalid timestamp sequence",
        )

    def _fare_reconciliation(self) -> None:
        if "rides" not in self.tables or "vehicles" not in self.tables:
            return
        rides = self.tables["rides"]
        vehicles = self.tables["vehicles"].set_index("vehicle_id")
        completed = rides[rides["ride_status"].astype(str).str.lower() == "completed"].copy()
        mismatches = 0
        checked = 0
        for _, row in completed.iterrows():
            if pd.isna(row.get("vehicle_id")) or row["vehicle_id"] not in vehicles.index:
                continue
            vtype = vehicles.loc[row["vehicle_id"], "vehicle_type"]
            if isinstance(vtype, pd.Series):
                vtype = vtype.iloc[0]
            expected = calculate_fare(
                vehicle_type=str(vtype),
                distance_km=float(row.get("distance_km") or 0),
                duration_minutes=float(row.get("duration_minutes") or 0),
                surge_multiplier=float(row.get("surge_multiplier") or 1),
                toll_amount=float(row.get("toll_amount") or 0),
                discount_amount=float(row.get("discount_amount") or 0),
            )
            actual = float(row.get("total_fare") or 0)
            checked += 1
            if abs(actual - expected["total_fare"]) > self.fare_tolerance:
                mismatches += 1
        status = "PASS" if mismatches == 0 else ("WARNING" if mismatches / max(checked, 1) < 0.01 else "FAIL")
        self._add(
            check_name="fare_reconciliation",
            table_name="rides",
            status=status,
            expected=0,
            actual=mismatches,
            message=f"{mismatches}/{checked} completed rides fail fare reconciliation (tol={self.fare_tolerance})",
        )

    def _status_checks(self) -> None:
        if "rides" in self.tables:
            statuses = self.tables["rides"]["ride_status"].astype(str)
            # Normalize for intentional capitalization issues
            bad = int((~statuses.isin(self.VALID_RIDE_STATUSES)).sum())
            self._add(
                check_name="valid_ride_status",
                table_name="rides",
                status="PASS" if bad == 0 else "FAIL",
                expected=0,
                actual=bad,
                message=f"{bad} rides with invalid ride_status",
            )
        if "payments" in self.tables:
            statuses = self.tables["payments"]["payment_status"].astype(str)
            bad = int((~statuses.isin(self.VALID_PAYMENT_STATUSES)).sum())
            self._add(
                check_name="valid_payment_status",
                table_name="payments",
                status="PASS" if bad == 0 else "FAIL",
                expected=0,
                actual=bad,
                message=f"{bad} payments with invalid payment_status",
            )


def run_validation(data_dir: Optional[Path] = None) -> Dict[str, Any]:
    framework = DataQualityFramework(data_dir=data_dir)
    results = framework.run_all()
    settings = get_settings()
    out = settings.processed_dir / "dq_results.json"
    framework.save_results(out)
    summary = framework.summary()
    return {"summary": summary, "results": results, "output": str(out)}
