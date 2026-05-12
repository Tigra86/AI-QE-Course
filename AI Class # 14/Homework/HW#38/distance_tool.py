import sys
import math

# --------------------------------------
# Haversine Formula
# --------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2 +
        math.cos(phi1) * math.cos(phi2) *
        math.sin(dlambda / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Distance in kilometers


# --------------------------------------
# CLI
# --------------------------------------

def main():

    if len(sys.argv) < 5:
        print("Usage:")
        print("python distance_cli.py <lat1> <lon1> <lat2> <lon2> [unit]")
        print("unit: km (default) or miles")
        return

    try:
        lat1 = float(sys.argv[1])
        lon1 = float(sys.argv[2])
        lat2 = float(sys.argv[3])
        lon2 = float(sys.argv[4])
    except ValueError:
        print("Error: Latitude and longitude must be numeric.")
        return

    unit = sys.argv[5].lower() if len(sys.argv) > 5 else "km"

    distance_km = haversine(lat1, lon1, lat2, lon2)

    if unit in ["miles", "mi"]:
        distance = distance_km * 0.621371
        print(f"Distance: {round(distance, 2)} miles")
    else:
        print(f"Distance: {round(distance_km, 2)} km")


if __name__ == "__main__":
    main()
    