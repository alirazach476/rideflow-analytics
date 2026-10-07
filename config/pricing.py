"""
RideFlow synthetic pricing model.

Formula (documented for reproducibility):

  distance_fare = distance_km * price_per_km[vehicle_type]
  time_fare     = duration_minutes * price_per_minute[vehicle_type]

  subtotal = (
      base_fare[vehicle_type]
      + distance_fare
      + time_fare
      + booking_fee
      + toll_amount
  ) * surge_multiplier

  tax_amount = subtotal * TAX_RATE
  total_fare = max(0, subtotal - discount_amount + tax_amount)

All amounts are in a fictional currency unit (RFU — RideFlow Units).
"""

from __future__ import annotations

from typing import Dict, Tuple

TAX_RATE = 0.08

# base_fare, price_per_km, price_per_minute, booking_fee, capacity
VEHICLE_PRICING: Dict[str, Dict[str, float]] = {
    "Bike": {
        "base_fare": 30.0,
        "price_per_km": 8.0,
        "price_per_minute": 1.0,
        "booking_fee": 5.0,
        "capacity": 1,
    },
    "Economy": {
        "base_fare": 50.0,
        "price_per_km": 12.0,
        "price_per_minute": 1.5,
        "booking_fee": 10.0,
        "capacity": 4,
    },
    "Sedan": {
        "base_fare": 70.0,
        "price_per_km": 15.0,
        "price_per_minute": 2.0,
        "booking_fee": 12.0,
        "capacity": 4,
    },
    "SUV": {
        "base_fare": 100.0,
        "price_per_km": 20.0,
        "price_per_minute": 2.5,
        "booking_fee": 15.0,
        "capacity": 6,
    },
    "Premium": {
        "base_fare": 150.0,
        "price_per_km": 30.0,
        "price_per_minute": 4.0,
        "booking_fee": 25.0,
        "capacity": 4,
    },
    "Van": {
        "base_fare": 120.0,
        "price_per_km": 22.0,
        "price_per_minute": 3.0,
        "booking_fee": 18.0,
        "capacity": 8,
    },
}

SURGE_LEVELS: Tuple[float, ...] = (1.0, 1.2, 1.5, 2.0, 2.5)

# Peak hours (local synthetic business rules)
MORNING_PEAK = range(7, 10)  # 07:00–09:59
EVENING_PEAK = range(17, 21)  # 17:00–20:59
LATE_NIGHT = range(0, 5)  # 00:00–04:59


def calculate_fare(
    vehicle_type: str,
    distance_km: float,
    duration_minutes: float,
    surge_multiplier: float,
    toll_amount: float = 0.0,
    discount_amount: float = 0.0,
) -> Dict[str, float]:
    """Calculate fare components using the RideFlow pricing formula."""
    pricing = VEHICLE_PRICING[vehicle_type]
    base_fare = pricing["base_fare"]
    booking_fee = pricing["booking_fee"]
    distance_fare = distance_km * pricing["price_per_km"]
    time_fare = duration_minutes * pricing["price_per_minute"]

    subtotal = (
        base_fare + distance_fare + time_fare + booking_fee + toll_amount
    ) * surge_multiplier
    tax_amount = round(subtotal * TAX_RATE, 2)
    total_fare = max(0.0, round(subtotal - discount_amount + tax_amount, 2))

    return {
        "base_fare": round(base_fare, 2),
        "distance_fare": round(distance_fare, 2),
        "time_fare": round(time_fare, 2),
        "booking_fee": round(booking_fee, 2),
        "toll_amount": round(toll_amount, 2),
        "discount_amount": round(discount_amount, 2),
        "tax_amount": tax_amount,
        "surge_multiplier": round(surge_multiplier, 2),
        "total_fare": total_fare,
    }
