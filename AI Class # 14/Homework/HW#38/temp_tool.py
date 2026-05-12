# python temp.py "Los Angeles, CA" -C
# python temp.py "Los Angeles, CA" -F

import requests
import argparse
import json

def get_lat_lon(city_state):
    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": city_state,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }

    headers = {
        "User-Agent": "ai-class-demo/1.0 (qa@gmail.com)"
    }

    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    data = response.json()

    if not data:
        raise ValueError(f"Location not found for: {city_state}")

    return float(data[0]["lat"]), float(data[0]["lon"])

def get_current_temperature(latitude, longitude, unit):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        f"&current_weather=true"
        f"&temperature_unit={unit}"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    return data["current_weather"]["temperature"]

def main():
    parser = argparse.ArgumentParser(description="Get current temperature for a city.")
    parser.add_argument("city", help='City and state in quotes, e.g. "Los Angeles, CA"')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-F", action="store_true", help="Return temperature in Fahrenheit")
    group.add_argument("-C", action="store_true", help="Return temperature in Celsius")

    args = parser.parse_args()

    unit_api = "fahrenheit" if args.F else "celsius"
    unit_label = "F" if args.F else "C"

    lat, lon = get_lat_lon(args.city)
    temp = get_current_temperature(lat, lon, unit_api)

    output = {
        "temperature": float(f"{float(temp):.1f}"),
        "unit": unit_label
    }

    inner_json = json.dumps(output)
    escaped = inner_json.replace('"', '\\"')

    print(f'"output": "{escaped}"')


if __name__ == "__main__":
    main()
