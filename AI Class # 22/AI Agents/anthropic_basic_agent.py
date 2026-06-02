from __future__ import annotations

import logging
import math
from typing import Any, Callable, Dict, List, Tuple
from urllib.parse import quote

import requests
from anthropic import Anthropic

logger = logging.getLogger(__name__)
client = Anthropic()

MODEL = "claude-opus-4-6"
MAX_TOKENS = 16000

def _geocode(city: str) -> Tuple[float, float, str]:
    resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json().get("results")
    if not results:
        raise ValueError(f"City not found: {city}")
    r = results[0]
    name = f"{r['name']}, {r.get('country', '')}"
    return r["latitude"], r["longitude"], name

def get_weather(city: str) -> str:
    try:
        lat, lon, name = _geocode(city)
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "wind_speed_unit": "kmh",
            },
            timeout=10,
        )
        resp.raise_for_status()
        cur = resp.json()["current"]

        wmo = _wmo_description(cur["weather_code"])
        return (
            f"{name}: {cur['temperature_2m']} °C, "
            f"{wmo}, "
            f"humidity {cur['relative_humidity_2m']}%, "
            f"wind {cur['wind_speed_10m']} km/h"
        )
    except Exception as e:
        return f"Weather error: {e}"


def get_distance(from_city: str, to_city: str) -> str:
    try:
        lat1, lon1, name1 = _geocode(from_city)
        lat2, lon2, name2 = _geocode(to_city)
        km = _haversine(lat1, lon1, lat2, lon2)
        return f"{name1} → {name2}: {km:,.0f} km (straight line)"
    except Exception as e:
        return f"Distance error: {e}"


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _wmo_description(code: int) -> str:
    descriptions = {
        0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
        45: "foggy", 48: "depositing rime fog",
        51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
        61: "slight rain", 63: "moderate rain", 65: "heavy rain",
        71: "slight snow", 73: "moderate snow", 75: "heavy snow",
        80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
        95: "thunderstorm", 96: "thunderstorm with slight hail", 99: "thunderstorm with heavy hail",
    }
    return descriptions.get(code, f"weather code {code}")

TOOL_FUNCTIONS: Dict[str, Callable[..., str]] = {
    "get_weather": get_weather,
    "get_distance": get_distance,
}

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "get_weather",
        "description": "Get the current real weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'Paris'.",
                },
            },
            "required": ["city"],
        },
    },
    {
        "name": "get_distance",
        "description": "Get the straight-line distance between two cities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_city": {
                    "type": "string",
                    "description": "Origin city, e.g. 'London'.",
                },
                "to_city": {
                    "type": "string",
                    "description": "Destination city, e.g. 'Riga'.",
                },
            },
            "required": ["from_city", "to_city"],
        },
    },
]

def agent(user_input: str) -> str:
    messages: List[Dict[str, Any]] = [
        {"role": "user", "content": user_input},
    ]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        text_parts: List[str] = []
        tool_uses = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        if response.stop_reason == "end_turn" or not tool_uses:
            return "\n".join(text_parts) if text_parts else "No response."

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tool_use in tool_uses:
            fn = TOOL_FUNCTIONS.get(tool_use.name)
            if fn:
                result = fn(**tool_use.input)
            else:
                result = f"Unknown tool: {tool_use.name}"

            logger.info("[%s] → %s", tool_use.name, result)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result,
            })

        messages.append({"role": "user", "content": tool_results})

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    answer = agent("What's the weather in Paris, and how far is it from London to Riga?")
    print(answer)
