from math import asin, cos, radians, sin, sqrt


def dms_to_decimal(degrees: float, minutes: float, seconds: float, reference: str) -> float:
    value = degrees + minutes / 60 + seconds / 3600
    if reference.upper() in {"S", "W"}:
        value *= -1
    if not -180 <= value <= 180:
        raise ValueError("Coordinate is outside valid range")
    return value


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0088
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def speed_kmh(distance_km: float, interval_seconds: float) -> float | None:
    return None if interval_seconds <= 0 else distance_km / (interval_seconds / 3600)
