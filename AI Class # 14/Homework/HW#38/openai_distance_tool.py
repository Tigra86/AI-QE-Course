import math
import json
import sys
import time
import requests
from datetime import datetime
from openai import OpenAI

MODEL = "gpt-5.2"
client = OpenAI()

GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

# --------------------------------------------------
# Debug Logger
# --------------------------------------------------

def log_step(title, payload=None):
    print("\n" + "=" * 60)
    print(f"[{datetime.utcnow().isoformat()}] {title}")
    print("=" * 60 + "\n")

    if payload is None:
        return

    try:
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()

        if isinstance(payload, list):
            payload = [
                item.model_dump() if hasattr(item, "model_dump") else item
                for item in payload
            ]

        print(json.dumps(payload, indent=2))
    except Exception:
        print(payload)

# --------------------------------------------------
# Geocoding via Nominatim
# --------------------------------------------------

def get_lat_lon(city):

    time.sleep(1)

    response = requests.get(
        GEOCODE_URL,
        params={
            "q": city,
            "format": "json",
            "limit": 1
        },
        headers={"User-Agent": "ai-class-demo/1.0 (aa@gmail.com)"},
        timeout=10
    )

    response.raise_for_status()
    data = response.json()

    if not data:
        raise ValueError(f"Location not found: {city}")

    return float(data[0]["lat"]), float(data[0]["lon"])

# --------------------------------------------------
# Haversine
# --------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
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

    return R * c

# --------------------------------------------------
# Tool Execution
# --------------------------------------------------

def calculate_distance(origin, destination, unit="km"):

    lat1, lon1 = get_lat_lon(origin)
    lat2, lon2 = get_lat_lon(destination)

    distance_km = haversine(lat1, lon1, lat2, lon2)

    if unit.lower() in ["miles", "mi"]:
        return {
            "origin": origin,
            "destination": destination,
            "distance": round(distance_km * 0.621371, 2),
            "unit": "miles"
        }

    return {
        "origin": origin,
        "destination": destination,
        "distance": round(distance_km, 2),
        "unit": "kilometers"
    }

# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    if len(sys.argv) < 2:
        print('Usage: python openai_distance_tool.py "Question"')
        print('Usage: python openai_distance_tool.py "What is the distance between Riga and London in km?"')
        return

    user_question = sys.argv[1]
    log_step("USER QUESTION", user_question)

    response = client.responses.create(
        model=MODEL,
        tool_choice="required",
        input=[
            {
                "role": "system",
                "content": "You must call calculate_distance for any distance question."
            },
            {
                "role": "user",
                "content": user_question
            }
        ],
        tools=[
            {
                "type": "function",
                "name": "calculate_distance",
                "description": "Calculate distance between two cities",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string"},
                        "destination": {"type": "string"},
                        "unit": {"type": "string"}
                    },
                    "required": ["origin", "destination"]
                }
            }
        ]
    )

    log_step("STEP 1 RESPONSE", response.output)

    tool_call = next(
        (item for item in response.output if item.type == "function_call"),
        None
    )

    if not tool_call:
        print("No tool call detected.")
        return

    args = tool_call.arguments

    if isinstance(args, str):
        args = json.loads(args)

    log_step("TOOL CALL", args)

    try:
        tool_result = calculate_distance(
            args["origin"],
            args["destination"],
            args.get("unit", "km")
        )
    except Exception as e:
        print("Tool error:", str(e))
        return

    log_step("TOOL RESULT", tool_result)

    final_response = client.responses.create(
        model=MODEL,
        previous_response_id=response.id,
        input=[
            {
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": json.dumps(tool_result)
            }
        ]
    )

    print("\nFINAL ANSWER:")
    print(final_response.output_text)


if __name__ == "__main__":
    main()