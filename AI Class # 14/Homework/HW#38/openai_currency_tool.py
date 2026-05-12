import requests
import json
import sys
from datetime import datetime
from openai import OpenAI

# ---------------------------------------
# CONFIG
# ---------------------------------------

MODEL = "gpt-5.2"
FX_API = "https://api.frankfurter.app/latest"

client = OpenAI()

def log_step(title, payload=None):
    print("\n" + "=" * 60)
    print(f"[{datetime.utcnow().isoformat()}] {title}")
    print("=" * 60 + "\n")

    if payload:
        try:
            if hasattr(payload, "model_dump"):
                payload = payload.model_dump()
            print(json.dumps(payload, indent=2))
        except Exception:
            print(payload)


# ---------------------------------------
# REAL CURRENCY API EXECUTION
# ---------------------------------------

def convert_currency(amount, from_currency, to_currency):

    params = {
        "amount": amount,
        "from": from_currency.upper(),
        "to": to_currency.upper()
    }

    response = requests.get(FX_API, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    if "rates" not in data or to_currency.upper() not in data["rates"]:
        raise ValueError("Invalid currency conversion")

    converted = round(data["rates"][to_currency.upper()], 2)

    return {
        "amount": amount,
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "converted_amount": converted
    }

# ---------------------------------------
# MAIN
# ---------------------------------------

def main():

    if len(sys.argv) < 2:
        print('Usage: python openai_currency_tool.py "Your question here"')
        return

    user_question = sys.argv[1]

    log_step("USER QUESTION", user_question)

    # ---------------------------------------
    # STEP 1 — Ask OpenAI
    # ---------------------------------------

    response = client.responses.create(
        model=MODEL,
        tool_choice="required",
        input=[
            {
                "role": "system",
                "content": "You must call convert_currency for any currency conversion question. Never calculate manually."
            },
            {
                "role": "user",
                "content": user_question
            }
        ],
        tools=[
            {
                "type": "function",
                "name": "convert_currency",
                "description": "Convert amount between currencies using latest exchange rate",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "from_currency": {"type": "string"},
                        "to_currency": {"type": "string"}
                    },
                    "required": ["amount", "from_currency", "to_currency"],
                    "additionalProperties": False
                }
            }
        ]
    )

    log_step("STEP 1 RESPONSE (RAW)", response.output)

    tool_call = None
    for item in response.output:
        if item.type == "function_call":
            tool_call = item
            break

    if not tool_call:
        print("No tool call detected.")
        return

    args = tool_call.arguments

    if isinstance(args, str):
        args = json.loads(args)

    log_step("TOOL CALL DETECTED", {
        "name": tool_call.name,
        "arguments": args,
        "call_id": tool_call.call_id,
        "previous_response_id": response.id
    })

    # ---------------------------------------
    # TOOL EXECUTION
    # ---------------------------------------

    tool_result = convert_currency(
        args["amount"],
        args["from_currency"],
        args["to_currency"]
    )

    log_step("TOOL EXECUTION RESULT", tool_result)

    # ---------------------------------------
    # STEP 2 — Send Tool
    # ---------------------------------------

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

    log_step("STEP 2 FINAL RESPONSE (RAW)", final_response.output)

    print("\nFINAL ANSWER:")
    print(final_response.output_text)


if __name__ == "__main__":
    main()