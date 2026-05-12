import requests
import sys
import time


def get_lat_lon(city_state):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city_state,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "ai-class/1.0 (qa@gmail.com)"
    }

    # Nominatim requires polite rate limiting
    time.sleep(1)

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        return None

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])

    return lat, lon


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print('python geocode_tool.py "City, State/Country"')
        return

    city_input = sys.argv[1]

    try:
        coords = get_lat_lon(city_input)

        if coords is None:
            print("Location not found.")
        else:
            print(f"Latitude:  {coords[0]}")
            print(f"Longitude: {coords[1]}")
            print(f"-----------------------")
            print(f"{coords[0]} {coords[1]}")

    except requests.exceptions.HTTPError as e:
        print("HTTP Error:", e)
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    main()

