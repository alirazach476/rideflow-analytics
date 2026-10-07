"""Tests for synthetic data generation."""

from __future__ import annotations

from datetime import date

from config.pricing import calculate_fare
from src.data_generation.generators import RideFlowGenerator


def test_cities_unique(small_generator: RideFlowGenerator):
    cities = small_generator.generate_cities(10)
    ids = [c["city_id"] for c in cities]
    assert len(ids) == len(set(ids))
    assert all(c["city_name"] for c in cities)


def test_users_required_fields(small_generator: RideFlowGenerator):
    cities = small_generator.generate_cities(5)
    users = small_generator.generate_users(100, cities, date(2024, 1, 1), date(2025, 1, 1))
    assert len(users) == 100
    assert len({u["user_id"] for u in users}) == 100
    for u in users:
        assert u["user_type"] in {"Regular", "Frequent", "Business", "Student", "Premium", "Occasional"}
        assert u["status"] in {"Active", "Inactive", "Suspended"}


def test_driver_ratings_in_range(small_generator: RideFlowGenerator):
    cities = small_generator.generate_cities(5)
    drivers = small_generator.generate_drivers(50, cities, date(2024, 1, 1), date(2025, 1, 1))
    for d in drivers:
        assert 3.5 <= d["rating"] <= 5.0


def test_fare_formula_non_negative():
    fare = calculate_fare("Economy", distance_km=5, duration_minutes=15, surge_multiplier=1.5, toll_amount=20, discount_amount=10)
    assert fare["total_fare"] >= 0
    assert fare["surge_multiplier"] == 1.5


def test_ride_timestamp_order_for_completed(small_generator: RideFlowGenerator):
    cities = small_generator.generate_cities(3)
    zones = small_generator.generate_zones(cities, 12)
    users = small_generator.generate_users(80, cities, date(2024, 1, 1), date(2025, 6, 1))
    drivers = small_generator.generate_drivers(20, cities, date(2024, 1, 1), date(2025, 6, 1))
    vehicles = small_generator.generate_vehicles(22, drivers)
    promos = small_generator.generate_promotions(5, date(2024, 1, 1), date(2025, 6, 1))
    rides, payments, ratings = small_generator.generate_rides(
        300, users, drivers, vehicles, zones, promos, date(2024, 1, 1), date(2025, 6, 1)
    )
    completed = [r for r in rides if r["ride_status"] == "Completed"]
    assert len(completed) > 50
    for r in completed:
        assert r["request_timestamp"] < r["accepted_timestamp"] < r["pickup_timestamp"] < r["dropoff_timestamp"]
        assert r["total_fare"] is not None and r["total_fare"] >= 0
        assert r["distance_km"] > 0
    assert len(payments) == len(completed)
    assert all(p["amount"] >= 0 for p in payments)
