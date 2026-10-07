"""Shared constants for synthetic RideFlow data."""

from __future__ import annotations

CITIES = [
    {"city_name": "Lahore", "country": "PK", "lat": 31.5204, "lon": 74.3587, "timezone": "Asia/Karachi"},
    {"city_name": "Karachi", "country": "PK", "lat": 24.8607, "lon": 67.0011, "timezone": "Asia/Karachi"},
    {"city_name": "Islamabad", "country": "PK", "lat": 33.6844, "lon": 73.0479, "timezone": "Asia/Karachi"},
    {"city_name": "Rawalpindi", "country": "PK", "lat": 33.5651, "lon": 73.0169, "timezone": "Asia/Karachi"},
    {"city_name": "Faisalabad", "country": "PK", "lat": 31.4504, "lon": 73.1350, "timezone": "Asia/Karachi"},
    {"city_name": "Multan", "country": "PK", "lat": 30.1575, "lon": 71.5249, "timezone": "Asia/Karachi"},
    {"city_name": "Peshawar", "country": "PK", "lat": 34.0151, "lon": 71.5249, "timezone": "Asia/Karachi"},
    {"city_name": "Gujranwala", "country": "PK", "lat": 32.1877, "lon": 74.1945, "timezone": "Asia/Karachi"},
    {"city_name": "Sialkot", "country": "PK", "lat": 32.4945, "lon": 74.5229, "timezone": "Asia/Karachi"},
    {"city_name": "Quetta", "country": "PK", "lat": 30.1798, "lon": 66.9750, "timezone": "Asia/Karachi"},
]

ZONE_TYPES = [
    "Residential",
    "Commercial",
    "Airport",
    "University",
    "Business District",
    "Shopping",
    "Industrial",
    "Entertainment",
    "Mixed",
]

USER_TYPES = ["Regular", "Frequent", "Business", "Student", "Premium", "Occasional"]
USER_STATUSES = ["Active", "Inactive", "Suspended"]
SIGNUP_CHANNELS = ["Organic", "Referral", "App Store", "Google Ads", "Partner", "Social"]

DRIVER_TYPES = ["Regular", "Part-Time", "Full-Time", "Premium"]
DRIVER_STATUSES = ["Active", "Inactive", "Suspended"]

VEHICLE_TYPES = ["Bike", "Economy", "Sedan", "SUV", "Premium", "Van"]
FUEL_TYPES = ["Petrol", "Diesel", "Hybrid", "Electric"]
VEHICLE_STATUSES = ["Active", "Inactive", "Maintenance"]

VEHICLE_MAKES = {
    "Bike": [("Honda", "CG125"), ("Yamaha", "YBR"), ("Suzuki", "GD110")],
    "Economy": [("Suzuki", "Cultus"), ("Toyota", "Vitz"), ("Honda", "City")],
    "Sedan": [("Toyota", "Corolla"), ("Honda", "Civic"), ("Hyundai", "Elantra")],
    "SUV": [("Toyota", "Fortuner"), ("Honda", "BR-V"), ("Kia", "Sportage")],
    "Premium": [("Mercedes", "C-Class"), ("BMW", "3 Series"), ("Audi", "A4")],
    "Van": [("Toyota", "Hiace"), ("Suzuki", "Every"), ("Hyundai", "H1")],
}

RIDE_STATUSES = [
    "Requested",
    "Accepted",
    "Driver_Cancelled",
    "Rider_Cancelled",
    "Completed",
    "No_Driver_Available",
]

# Approximate status distribution for realistic behavior
RIDE_STATUS_WEIGHTS = {
    "Completed": 0.72,
    "Rider_Cancelled": 0.12,
    "Driver_Cancelled": 0.08,
    "No_Driver_Available": 0.05,
    "Accepted": 0.02,
    "Requested": 0.01,
}

PAYMENT_METHODS = ["Cash", "Credit Card", "Debit Card", "Mobile Wallet", "Bank Transfer"]
PAYMENT_METHOD_WEIGHTS = [0.35, 0.20, 0.15, 0.25, 0.05]
PAYMENT_STATUSES = ["Completed", "Failed", "Refunded", "Pending"]
TRANSACTION_TYPES = ["Ride Payment", "Refund", "Adjustment"]

RIDER_CANCEL_REASONS = ["Long ETA", "High Fare", "Driver Delayed", "Changed Mind", "Other"]
DRIVER_CANCEL_REASONS = ["Too Far", "Low Fare", "Traffic", "Vehicle Issue", "Personal Reason", "Other"]

RATING_CATEGORIES = {
    5: "Excellent",
    4: "Good",
    3: "Average",
    2: "Poor",
    1: "Very Poor",
}

PROMOTION_TYPES = ["Percentage", "Fixed Amount", "First Ride", "Referral", "Weekend", "Peak Hour"]

# User type behavioral multipliers for ride frequency
USER_RIDE_WEIGHTS = {
    "Frequent": 3.5,
    "Business": 2.2,
    "Premium": 2.0,
    "Regular": 1.0,
    "Student": 1.3,
    "Occasional": 0.35,
}

# Preferred vehicle weights by user type
USER_VEHICLE_PREFS = {
    "Premium": {"Premium": 0.45, "SUV": 0.25, "Sedan": 0.20, "Economy": 0.05, "Van": 0.03, "Bike": 0.02},
    "Business": {"Sedan": 0.35, "SUV": 0.25, "Premium": 0.20, "Economy": 0.12, "Van": 0.05, "Bike": 0.03},
    "Student": {"Bike": 0.35, "Economy": 0.40, "Sedan": 0.15, "SUV": 0.05, "Van": 0.03, "Premium": 0.02},
    "Frequent": {"Economy": 0.35, "Sedan": 0.30, "Bike": 0.15, "SUV": 0.12, "Van": 0.05, "Premium": 0.03},
    "Regular": {"Economy": 0.40, "Sedan": 0.25, "Bike": 0.15, "SUV": 0.12, "Van": 0.05, "Premium": 0.03},
    "Occasional": {"Economy": 0.45, "Sedan": 0.25, "Bike": 0.12, "SUV": 0.10, "Van": 0.05, "Premium": 0.03},
}

GENDERS = ["Male", "Female", "Other"]
GENDER_WEIGHTS = [0.55, 0.43, 0.02]
