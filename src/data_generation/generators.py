"""Synthetic entity generators for RideFlow."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from faker import Faker

from config.pricing import (
    EVENING_PEAK,
    LATE_NIGHT,
    MORNING_PEAK,
    VEHICLE_PRICING,
    calculate_fare,
)
from src.data_generation.constants import (
    CITIES,
    DRIVER_CANCEL_REASONS,
    DRIVER_STATUSES,
    DRIVER_TYPES,
    FUEL_TYPES,
    GENDER_WEIGHTS,
    GENDERS,
    PAYMENT_METHOD_WEIGHTS,
    PAYMENT_METHODS,
    PAYMENT_STATUSES,
    PROMOTION_TYPES,
    RATING_CATEGORIES,
    RIDER_CANCEL_REASONS,
    RIDE_STATUS_WEIGHTS,
    SIGNUP_CHANNELS,
    USER_RIDE_WEIGHTS,
    USER_STATUSES,
    USER_TYPES,
    USER_VEHICLE_PREFS,
    VEHICLE_MAKES,
    VEHICLE_STATUSES,
    VEHICLE_TYPES,
    ZONE_TYPES,
)


class RideFlowGenerator:
    """Generates a coherent synthetic RideFlow dataset."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.fake = Faker()
        Faker.seed(seed)

    # ------------------------------------------------------------------ cities
    def generate_cities(self, n: int = 10) -> List[Dict[str, Any]]:
        rows = []
        for i, city in enumerate(CITIES[:n], start=1):
            rows.append(
                {
                    "city_id": i,
                    "city_name": city["city_name"],
                    "country": city["country"],
                    "latitude": city["lat"],
                    "longitude": city["lon"],
                    "timezone": city["timezone"],
                    "population_tier": self.rng.choice(["Tier1", "Tier2", "Tier3"], p=[0.3, 0.4, 0.3]),
                    "is_active": True,
                }
            )
        return rows

    # ------------------------------------------------------------------ zones
    def generate_zones(self, cities: List[Dict[str, Any]], n_zones: int = 100) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        zones_per_city = max(1, n_zones // len(cities))
        zone_id = 1
        for city in cities:
            for z in range(zones_per_city):
                ztype = ZONE_TYPES[z % len(ZONE_TYPES)]
                lat_offset = float(self.rng.uniform(-0.15, 0.15))
                lon_offset = float(self.rng.uniform(-0.15, 0.15))
                rows.append(
                    {
                        "zone_id": zone_id,
                        "city_id": city["city_id"],
                        "zone_name": f"{city['city_name']} {ztype} {z + 1}",
                        "zone_type": ztype,
                        "latitude_center": round(city["latitude"] + lat_offset, 6),
                        "longitude_center": round(city["longitude"] + lon_offset, 6),
                        "demand_index": round(float(self.rng.uniform(0.4, 1.6)), 2),
                    }
                )
                zone_id += 1
        # Fill remaining to hit n_zones
        while len(rows) < n_zones:
            city = cities[len(rows) % len(cities)]
            ztype = self.rng.choice(ZONE_TYPES)
            rows.append(
                {
                    "zone_id": zone_id,
                    "city_id": city["city_id"],
                    "zone_name": f"{city['city_name']} {ztype} Extra {zone_id}",
                    "zone_type": ztype,
                    "latitude_center": round(city["latitude"] + float(self.rng.uniform(-0.2, 0.2)), 6),
                    "longitude_center": round(city["longitude"] + float(self.rng.uniform(-0.2, 0.2)), 6),
                    "demand_index": round(float(self.rng.uniform(0.4, 1.6)), 2),
                }
            )
            zone_id += 1
        return rows[:n_zones]

    # ------------------------------------------------------------------ users
    def generate_users(
        self,
        n: int,
        cities: List[Dict[str, Any]],
        start: date,
        end: date,
    ) -> List[Dict[str, Any]]:
        rows = []
        city_ids = [c["city_id"] for c in cities]
        # Larger cities get more users
        city_weights = np.array([0.18, 0.22, 0.10, 0.08, 0.10, 0.07, 0.08, 0.06, 0.06, 0.05][: len(city_ids)])
        city_weights = city_weights / city_weights.sum()

        for i in range(1, n + 1):
            dob = self.fake.date_of_birth(minimum_age=18, maximum_age=70)
            reg = self._random_date(start, end - timedelta(days=30))
            user_type = str(self.rng.choice(USER_TYPES, p=[0.35, 0.15, 0.12, 0.15, 0.08, 0.15]))
            status = str(self.rng.choice(USER_STATUSES, p=[0.82, 0.13, 0.05]))
            rows.append(
                {
                    "user_id": i,
                    "first_name": self.fake.first_name(),
                    "last_name": self.fake.last_name(),
                    "gender": str(self.rng.choice(GENDERS, p=GENDER_WEIGHTS)),
                    "date_of_birth": dob.isoformat(),
                    "registration_date": reg.isoformat(),
                    "city_id": int(self.rng.choice(city_ids, p=city_weights)),
                    "user_type": user_type,
                    "status": status,
                    "signup_channel": str(self.rng.choice(SIGNUP_CHANNELS)),
                    "updated_at": reg.isoformat() + "T00:00:00",
                }
            )
        return rows

    # ------------------------------------------------------------------ drivers
    def generate_drivers(
        self,
        n: int,
        cities: List[Dict[str, Any]],
        start: date,
        end: date,
    ) -> List[Dict[str, Any]]:
        rows = []
        city_ids = [c["city_id"] for c in cities]
        for i in range(1, n + 1):
            dob = self.fake.date_of_birth(minimum_age=21, maximum_age=60)
            reg = self._random_date(start, end - timedelta(days=60))
            driver_type = str(self.rng.choice(DRIVER_TYPES, p=[0.30, 0.25, 0.35, 0.10]))
            status = str(self.rng.choice(DRIVER_STATUSES, p=[0.80, 0.15, 0.05]))
            # Realistic ratings clustered 4.0–5.0
            rating = round(float(np.clip(self.rng.normal(4.55, 0.25), 3.5, 5.0)), 1)
            total_rides = int(self.rng.integers(0, 5000))
            if driver_type == "Full-Time":
                total_rides = int(self.rng.integers(500, 8000))
            elif driver_type == "Part-Time":
                total_rides = int(self.rng.integers(50, 1500))
            rows.append(
                {
                    "driver_id": i,
                    "first_name": self.fake.first_name(),
                    "last_name": self.fake.last_name(),
                    "gender": str(self.rng.choice(GENDERS, p=GENDER_WEIGHTS)),
                    "date_of_birth": dob.isoformat(),
                    "registration_date": reg.isoformat(),
                    "city_id": int(self.rng.choice(city_ids)),
                    "driver_type": driver_type,
                    "status": status,
                    "rating": rating,
                    "total_rides": total_rides,
                    "updated_at": reg.isoformat() + "T00:00:00",
                }
            )
        return rows

    # ------------------------------------------------------------------ vehicles
    def generate_vehicles(
        self,
        n: int,
        drivers: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        rows = []
        # Most drivers have 1 vehicle; some have 2
        assigned = 0
        driver_idx = 0
        while assigned < n and driver_idx < len(drivers):
            driver = drivers[driver_idx]
            vehicles_for_driver = 1 if assigned + 1 >= n or self.rng.random() > 0.1 else 2
            for _ in range(vehicles_for_driver):
                if assigned >= n:
                    break
                vtype = str(self.rng.choice(VEHICLE_TYPES, p=[0.12, 0.35, 0.25, 0.12, 0.08, 0.08]))
                if driver["driver_type"] == "Premium":
                    vtype = str(self.rng.choice(["Premium", "SUV", "Sedan"], p=[0.5, 0.3, 0.2]))
                make, model = VEHICLE_MAKES[vtype][int(self.rng.integers(0, len(VEHICLE_MAKES[vtype])))]
                capacity = int(VEHICLE_PRICING[vtype]["capacity"])
                fuel = str(self.rng.choice(FUEL_TYPES, p=[0.55, 0.15, 0.15, 0.15]))
                if vtype == "Bike":
                    fuel = "Petrol"
                    capacity = 1
                rows.append(
                    {
                        "vehicle_id": assigned + 1,
                        "driver_id": driver["driver_id"],
                        "vehicle_type": vtype,
                        "make": make,
                        "model": model,
                        "model_year": int(self.rng.integers(2015, 2026)),
                        "city_id": driver["city_id"],
                        "fuel_type": fuel,
                        "capacity": capacity,
                        "status": str(self.rng.choice(VEHICLE_STATUSES, p=[0.85, 0.10, 0.05])),
                    }
                )
                assigned += 1
            driver_idx += 1
        # If more vehicles than drivers, cycle
        while assigned < n:
            driver = drivers[assigned % len(drivers)]
            vtype = str(self.rng.choice(VEHICLE_TYPES))
            make, model = VEHICLE_MAKES[vtype][0]
            rows.append(
                {
                    "vehicle_id": assigned + 1,
                    "driver_id": driver["driver_id"],
                    "vehicle_type": vtype,
                    "make": make,
                    "model": model,
                    "model_year": int(self.rng.integers(2015, 2026)),
                    "city_id": driver["city_id"],
                    "fuel_type": str(self.rng.choice(FUEL_TYPES)),
                    "capacity": int(VEHICLE_PRICING[vtype]["capacity"]),
                    "status": "Active",
                }
            )
            assigned += 1
        return rows

    # ------------------------------------------------------------------ promotions
    def generate_promotions(self, n: int, start: date, end: date) -> List[Dict[str, Any]]:
        rows = []
        for i in range(1, n + 1):
            ptype = str(self.rng.choice(PROMOTION_TYPES))
            p_start = self._random_date(start, end - timedelta(days=30))
            p_end = p_start + timedelta(days=int(self.rng.integers(7, 90)))
            rows.append(
                {
                    "promotion_id": i,
                    "promotion_code": f"RF{ptype[:3].upper()}{i:04d}",
                    "promotion_type": ptype,
                    "discount_percentage": round(float(self.rng.choice([5, 10, 15, 20, 25])), 2),
                    "maximum_discount": round(float(self.rng.choice([50, 100, 150, 200, 300])), 2),
                    "start_date": p_start.isoformat(),
                    "end_date": min(p_end, end).isoformat(),
                    "target_user_type": str(self.rng.choice(USER_TYPES + ["All"])),
                }
            )
        return rows

    # ------------------------------------------------------------------ surge
    def compute_surge(
        self,
        hour: int,
        day_of_week: int,
        zone_demand: float,
        special_event: bool = False,
        weather_factor: float = 1.0,
    ) -> float:
        """Demand/supply-linked surge — not uniform random."""
        base = 1.0
        if hour in MORNING_PEAK or hour in EVENING_PEAK:
            base += 0.35
        elif hour in LATE_NIGHT:
            base += 0.15
        if day_of_week >= 5:  # weekend
            base += 0.15
        base += max(0.0, (zone_demand - 1.0) * 0.4)
        if special_event:
            base += 0.5
        base *= weather_factor
        # Quantize to documented levels
        levels = [1.0, 1.2, 1.5, 2.0, 2.5]
        return min(levels, key=lambda x: abs(x - base))

    # ------------------------------------------------------------------ rides
    def generate_rides(
        self,
        n: int,
        users: List[Dict[str, Any]],
        drivers: List[Dict[str, Any]],
        vehicles: List[Dict[str, Any]],
        zones: List[Dict[str, Any]],
        promotions: List[Dict[str, Any]],
        start: date,
        end: date,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Generate rides, payments, and ratings together for consistency."""
        # Indexes
        users_by_city: Dict[int, List[Dict[str, Any]]] = {}
        for u in users:
            if u["status"] != "Suspended":
                users_by_city.setdefault(u["city_id"], []).append(u)

        vehicles_by_driver = {v["driver_id"]: v for v in vehicles if v["status"] == "Active"}
        active_drivers = [d for d in drivers if d["status"] == "Active" and d["driver_id"] in vehicles_by_driver]
        drivers_by_city: Dict[int, List[Dict[str, Any]]] = {}
        for d in active_drivers:
            drivers_by_city.setdefault(d["city_id"], []).append(d)

        zones_by_city: Dict[int, List[Dict[str, Any]]] = {}
        for z in zones:
            zones_by_city.setdefault(z["city_id"], []).append(z)

        # Weighted user selection by ride propensity
        user_weights = np.array([USER_RIDE_WEIGHTS.get(u["user_type"], 1.0) for u in users], dtype=float)
        user_weights = user_weights / user_weights.sum()

        rides: List[Dict[str, Any]] = []
        payments: List[Dict[str, Any]] = []
        ratings: List[Dict[str, Any]] = []

        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())
        span_seconds = int((end_dt - start_dt).total_seconds())

        payment_id = 1
        rating_id = 1

        for ride_id in range(1, n + 1):
            user = users[int(self.rng.choice(len(users), p=user_weights))]
            city_id = user["city_id"]
            city_zones = zones_by_city.get(city_id) or zones
            city_drivers = drivers_by_city.get(city_id) or active_drivers

            pickup_zone = city_zones[int(self.rng.integers(0, len(city_zones)))]
            dropoff_zone = city_zones[int(self.rng.integers(0, len(city_zones)))]
            while dropoff_zone["zone_id"] == pickup_zone["zone_id"] and len(city_zones) > 1:
                dropoff_zone = city_zones[int(self.rng.integers(0, len(city_zones)))]

            request_ts = start_dt + timedelta(seconds=int(self.rng.integers(0, max(1, span_seconds))))
            hour = request_ts.hour
            dow = request_ts.weekday()
            special = self.rng.random() < 0.02
            weather = float(self.rng.choice([1.0, 1.0, 1.0, 1.1, 1.25], p=[0.7, 0.1, 0.05, 0.1, 0.05]))
            surge = self.compute_surge(hour, dow, pickup_zone["demand_index"], special, weather)

            # Status influenced by surge / supply
            status_probs = dict(RIDE_STATUS_WEIGHTS)
            if surge >= 2.0:
                status_probs["Rider_Cancelled"] += 0.04
                status_probs["No_Driver_Available"] += 0.03
                status_probs["Completed"] -= 0.07
            if not city_drivers:
                status = "No_Driver_Available"
            else:
                keys = list(status_probs.keys())
                probs = np.array([status_probs[k] for k in keys], dtype=float)
                probs = probs / probs.sum()
                status = str(self.rng.choice(keys, p=probs))

            driver = None
            vehicle = None
            if status not in ("Requested", "No_Driver_Available") and city_drivers:
                driver = city_drivers[int(self.rng.integers(0, len(city_drivers)))]
                vehicle = vehicles_by_driver[driver["driver_id"]]

            # Vehicle preference by user type
            if vehicle and user["user_type"] in USER_VEHICLE_PREFS:
                prefs = USER_VEHICLE_PREFS[user["user_type"]]
                # Soft preference: occasionally re-pick matching vehicle in city
                if self.rng.random() < 0.4:
                    preferred = str(self.rng.choice(list(prefs.keys()), p=list(prefs.values())))
                    matches = [
                        d
                        for d in city_drivers
                        if vehicles_by_driver[d["driver_id"]]["vehicle_type"] == preferred
                    ]
                    if matches:
                        driver = matches[int(self.rng.integers(0, len(matches)))]
                        vehicle = vehicles_by_driver[driver["driver_id"]]

            vehicle_type = vehicle["vehicle_type"] if vehicle else "Economy"

            accepted_ts = pickup_ts = dropoff_ts = None
            distance_km = duration_minutes = 0.0
            cancel_reason = None

            if status in ("Accepted", "Completed", "Driver_Cancelled", "Rider_Cancelled"):
                accepted_ts = request_ts + timedelta(seconds=int(self.rng.integers(15, 300)))
            if status in ("Completed", "Driver_Cancelled", "Rider_Cancelled") and accepted_ts:
                if status == "Driver_Cancelled":
                    cancel_reason = str(self.rng.choice(DRIVER_CANCEL_REASONS))
                elif status == "Rider_Cancelled":
                    # Higher cancel when surge high
                    cancel_reason = str(self.rng.choice(RIDER_CANCEL_REASONS))
                    if surge >= 1.5 and self.rng.random() < 0.4:
                        cancel_reason = "High Fare"
                else:
                    pickup_ts = accepted_ts + timedelta(seconds=int(self.rng.integers(60, 900)))
                    # Distance: airport/long trips sometimes longer
                    if pickup_zone["zone_type"] == "Airport" or dropoff_zone["zone_type"] == "Airport":
                        distance_km = round(float(self.rng.uniform(8, 35)), 2)
                    else:
                        distance_km = round(float(np.clip(self.rng.lognormal(1.5, 0.6), 0.8, 45)), 2)
                    avg_speed = float(self.rng.uniform(18, 35))  # km/h city traffic
                    duration_minutes = round(max(3.0, (distance_km / avg_speed) * 60 + float(self.rng.normal(0, 3))), 1)
                    dropoff_ts = pickup_ts + timedelta(minutes=duration_minutes)

            toll = round(float(self.rng.choice([0, 0, 0, 20, 50, 100], p=[0.7, 0.1, 0.05, 0.08, 0.05, 0.02])), 2)
            discount = 0.0
            if status == "Completed" and self.rng.random() < 0.15 and promotions:
                promo = promotions[int(self.rng.integers(0, len(promotions)))]
                # provisional discount based on rough fare estimate
                rough = VEHICLE_PRICING[vehicle_type]["base_fare"] + distance_km * 12
                discount = min(
                    promo["maximum_discount"],
                    round(rough * promo["discount_percentage"] / 100, 2),
                )

            fare = calculate_fare(
                vehicle_type=vehicle_type,
                distance_km=distance_km if status == "Completed" else 0,
                duration_minutes=duration_minutes if status == "Completed" else 0,
                surge_multiplier=surge,
                toll_amount=toll if status == "Completed" else 0,
                discount_amount=discount if status == "Completed" else 0,
            )

            payment_method = str(self.rng.choice(PAYMENT_METHODS, p=PAYMENT_METHOD_WEIGHTS))

            ride = {
                "ride_id": ride_id,
                "request_id": f"REQ{ride_id:08d}",
                "user_id": user["user_id"],
                "driver_id": driver["driver_id"] if driver else None,
                "vehicle_id": vehicle["vehicle_id"] if vehicle else None,
                "city_id": city_id,
                "pickup_zone_id": pickup_zone["zone_id"],
                "dropoff_zone_id": dropoff_zone["zone_id"],
                "request_timestamp": request_ts.isoformat(sep=" "),
                "accepted_timestamp": accepted_ts.isoformat(sep=" ") if accepted_ts else None,
                "pickup_timestamp": pickup_ts.isoformat(sep=" ") if pickup_ts else None,
                "dropoff_timestamp": dropoff_ts.isoformat(sep=" ") if dropoff_ts else None,
                "ride_status": status,
                "distance_km": distance_km if status == "Completed" else None,
                "duration_minutes": duration_minutes if status == "Completed" else None,
                "base_fare": fare["base_fare"] if status == "Completed" else None,
                "surge_multiplier": surge,
                "booking_fee": fare["booking_fee"] if status == "Completed" else None,
                "toll_amount": fare["toll_amount"] if status == "Completed" else None,
                "discount_amount": fare["discount_amount"] if status == "Completed" else None,
                "tax_amount": fare["tax_amount"] if status == "Completed" else None,
                "total_fare": fare["total_fare"] if status == "Completed" else None,
                "payment_method": payment_method if status == "Completed" else None,
                "cancellation_reason": cancel_reason,
                "cancelled_by": (
                    "Driver"
                    if status == "Driver_Cancelled"
                    else ("Rider" if status == "Rider_Cancelled" else None)
                ),
                "updated_at": (dropoff_ts or accepted_ts or request_ts).isoformat(sep=" "),
            }
            rides.append(ride)

            if status == "Completed":
                pay_status = str(self.rng.choice(PAYMENT_STATUSES, p=[0.92, 0.04, 0.02, 0.02]))
                payments.append(
                    {
                        "payment_id": payment_id,
                        "ride_id": ride_id,
                        "user_id": user["user_id"],
                        "payment_timestamp": dropoff_ts.isoformat(sep=" ") if dropoff_ts else request_ts.isoformat(sep=" "),
                        "payment_method": payment_method,
                        "amount": fare["total_fare"],
                        "payment_status": pay_status,
                        "transaction_type": "Ride Payment",
                    }
                )
                payment_id += 1

                # Ratings (~70% of completed rides get mutual ratings)
                if self.rng.random() < 0.70 and driver:
                    user_rating = int(np.clip(int(self.rng.choice([5, 4, 3, 2, 1], p=[0.45, 0.30, 0.15, 0.07, 0.03])), 1, 5))
                    ratings.append(
                        {
                            "rating_id": rating_id,
                            "ride_id": ride_id,
                            "user_id": user["user_id"],
                            "driver_id": driver["driver_id"],
                            "rating_from": "User",
                            "rating_to": "Driver",
                            "rating": user_rating,
                            "rating_timestamp": dropoff_ts.isoformat(sep=" "),
                            "comment_category": RATING_CATEGORIES[user_rating],
                        }
                    )
                    rating_id += 1
                if self.rng.random() < 0.55 and driver:
                    driver_rating = int(np.clip(int(self.rng.choice([5, 4, 3, 2, 1], p=[0.50, 0.30, 0.12, 0.05, 0.03])), 1, 5))
                    ratings.append(
                        {
                            "rating_id": rating_id,
                            "ride_id": ride_id,
                            "user_id": user["user_id"],
                            "driver_id": driver["driver_id"],
                            "rating_from": "Driver",
                            "rating_to": "User",
                            "rating": driver_rating,
                            "rating_timestamp": dropoff_ts.isoformat(sep=" "),
                            "comment_category": RATING_CATEGORIES[driver_rating],
                        }
                    )
                    rating_id += 1

        return rides, payments, ratings

    # ------------------------------------------------------------------ sessions
    def generate_driver_sessions(
        self,
        n: int,
        drivers: List[Dict[str, Any]],
        zones: List[Dict[str, Any]],
        start: date,
        end: date,
    ) -> List[Dict[str, Any]]:
        rows = []
        active = [d for d in drivers if d["status"] == "Active"]
        zones_by_city: Dict[int, List[Dict[str, Any]]] = {}
        for z in zones:
            zones_by_city.setdefault(z["city_id"], []).append(z)

        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.max.time())
        span = int((end_dt - start_dt).total_seconds())

        for i in range(1, n + 1):
            driver = active[int(self.rng.integers(0, len(active)))]
            city_zones = zones_by_city.get(driver["city_id"]) or zones
            zone = city_zones[int(self.rng.integers(0, len(city_zones)))]
            sess_start = start_dt + timedelta(seconds=int(self.rng.integers(0, max(1, span - 28800))))
            online_minutes = int(self.rng.integers(60, 480))
            if driver["driver_type"] == "Full-Time":
                online_minutes = int(self.rng.integers(240, 600))
            elif driver["driver_type"] == "Part-Time":
                online_minutes = int(self.rng.integers(60, 240))
            sess_end = sess_start + timedelta(minutes=online_minutes)
            rides_completed = int(self.rng.poisson(online_minutes / 45))
            rows.append(
                {
                    "session_id": i,
                    "driver_id": driver["driver_id"],
                    "city_id": driver["city_id"],
                    "zone_id": zone["zone_id"],
                    "session_start": sess_start.isoformat(sep=" "),
                    "session_end": sess_end.isoformat(sep=" "),
                    "online_minutes": online_minutes,
                    "rides_completed": rides_completed,
                }
            )
        return rows

    def _random_date(self, start: date, end: date) -> date:
        if end <= start:
            return start
        delta = (end - start).days
        return start + timedelta(days=int(self.rng.integers(0, delta + 1)))
