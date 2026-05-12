import requests
import json
import time
import sys
from openai import OpenAI
from datetime import datetime

client = OpenAI()

MODEL = "gpt-5.2"
GEO_API = "https://nominatim.openstreetmap.org/search"
WEATHER_API = "https://api.open-meteo.com/v1/forecast"

# ---------------------------------------
# Structured Logger
# ---------------------------------------

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
        print(str(payload))


# ---------------------------------------
# Geocoding
# ---------------------------------------

def get_lat_lon(city):
    params = {"q": city, "format": "json", "limit": 1}
    headers = {"User-Agent": "ai-class-demo/1.0 (qa@gmail.com)"}

    time.sleep(1)  # Required politeness for Nominatim

    log_step("GEOCODING REQUEST", {"url": GEO_API, "params": params})

    response = requests.get(GEO_API, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()

    if not data:
        raise ValueError("Location not found")

    lat = float(data[0]["lat"])
    lon = float(data[0]["lon"])

    log_step("GEOCODING RESPONSE", {"lat": lat, "lon": lon})

    return lat, lon


# ---------------------------------------
# Weather Tool Execution
# ---------------------------------------

def get_weather(city, unit):

    unit_api = "fahrenheit" if unit.upper() == "F" else "celsius"

    lat, lon = get_lat_lon(city)

    url = (
        f"{WEATHER_API}"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&current_weather=true"
        f"&temperature_unit={unit_api}"
    )

    log_step("WEATHER API REQUEST", {"url": url})

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    temp = float(f"{float(data['current_weather']['temperature']):.1f}")

    result = {
        "temperature": temp,
        "unit": "F" if unit.upper() == "F" else "C"
    }

    log_step("WEATHER API RESPONSE", result)

    return result


# ---------------------------------------
# Main Orchestration
# ---------------------------------------

def main():

    if len(sys.argv) < 3:
        print('Usage: python openai_get_weather_tool.py "City, State" -F|-C')
        print('Usage: python openai_get_weather_tool.py "What is the current temperature in San Francisco?" -F ')
        return

    input = sys.argv[1].replace("?", "")
    unit_flag = sys.argv[2]
    unit = "F" if unit_flag.upper() == "-F" else "C"

    user_question = (
        f"{input} in {'Fahrenheit' if unit == 'F' else 'Celsius'}?"
    )

    log_step("USER QUESTION", user_question)

    # ---------------------------------------
    # STEP 1 — Ask OpenAI
    # ---------------------------------------

    step1_payload = {
        "model": MODEL,
        "input": user_question,
        "tool_choice": "required",
        "tools": [
            {
                "type": "function",
                "name": "get_weather",
                "description": "Get current temperature for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "unit": {"type": "string"}
                    },
                    "required": ["city", "unit"],
                    "additionalProperties": False
                }
            }
        ]
    }

    log_step("REQUEST STEP 1 (OPENAI)", step1_payload)

    response = client.responses.create(**step1_payload)

    log_step("RESPONSE STEP 1 (OPENAI)", {
        "response_id": response.id,
        "status": response.status,
        "model": response.model,
        "output": [item.model_dump() for item in response.output]
    })

    # Extract tool call safely
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

    log_step("TOOL CALL DETECTED", {
        "tool_name": tool_call.name,
        "arguments": args,
        "call_id": tool_call.call_id,
        "previous_response_id": response.id
    })

    # ---------------------------------------
    # TOOL EXECUTION
    # ---------------------------------------

    tool_result = get_weather(args["city"], args["unit"])

    log_step("TOOL RESULT (LOCAL EXECUTION)", tool_result)

    # ---------------------------------------
    # STEP 2 — Return Tool Output to OpenAI
    # ---------------------------------------

    step2_payload = {
        "model": MODEL,
        "previous_response_id": response.id,
        "input": [
            {
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": json.dumps(tool_result)
            }
        ]
    }

    log_step("REQUEST STEP 2 (OPENAI)", step2_payload)

    final_response = client.responses.create(**step2_payload)

    log_step("RESPONSE STEP 2 (OPENAI)", {
        "response_id": final_response.id,
        "status": final_response.status,
        "output": [item.model_dump() for item in final_response.output]
    })

    print("\nFINAL ANSWER:")
    print(final_response.output_text)


if __name__ == "__main__":
    main()
