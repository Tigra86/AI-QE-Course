import sys
import json
import requests
from datetime import datetime
from openai import OpenAI

# -----------------------------
# CONFIG
# -----------------------------

API_URL = "https://alex.academy/ai/score/api.php"
MODEL = "gpt-5.2"

client = OpenAI()

# -----------------------------
# Structured Logger
# -----------------------------

def log_step(title, payload=None):
    print("\n" + "=" * 70)
    print(f"[{datetime.utcnow().isoformat()}] {title}")
    print("=" * 70)

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

# -----------------------------
# TOOL EXECUTION (PHP API)
# -----------------------------

def call_api(action, name=None, value=None):

    params = {"action": action}

    if name:
        params["name"] = name

    if value is not None:
        params["value"] = value

    log_step("DATABASE API REQUEST", params)

    response = requests.get(
        API_URL,
        params=params,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10
    )

    response.raise_for_status()
    result = response.json()

    log_step("DATABASE API RESPONSE", result)

    return result

# -----------------------------
# MAIN
# -----------------------------

def main():

    if len(sys.argv) < 2:
        print('Usage: python openai_database_query_tool.py "Your question here"')
        return

    user_question = sys.argv[1]

    log_step("USER QUESTION", user_question)

    # -----------------------------
    # STEP 1 — Ask OpenAI
    # -----------------------------

    step1_payload = {
        "model": MODEL,
        "tool_choice": "required",
        "input": [
            {
                "role": "system",
                "content": "You must answer database questions strictly by calling the most appropriate tool. Never answer from memory."
            },
            {
                "role": "user",
                "content": user_question
            }
        ],
        "tools": [
            {"type": "function", "name": "student_count",
             "description": "Get total number of students",
             "parameters": {"type": "object", "properties": {}}},

            {"type": "function", "name": "total_completed",
             "description": "Get total completed assignments",
             "parameters": {"type": "object", "properties": {}}},

            {"type": "function", "name": "expected_total",
             "description": "Get expected total assignments (students × assignments)",
             "parameters": {"type": "object", "properties": {}}},

            {"type": "function", "name": "search_student",
             "description": "Search student by name",
             "parameters": {
                 "type": "object",
                 "properties": {"name": {"type": "string"}},
                 "required": ["name"]
             }},

            {"type": "function", "name": "get_mean",
             "description": "Get mean completed assignments",
             "parameters": {"type": "object", "properties": {}}},

            {"type": "function", "name": "get_stddev",
             "description": "Get standard deviation",
             "parameters": {"type": "object", "properties": {}}},

            {"type": "function", "name": "completed_all",
             "description": "Students who completed all assignments",
             "parameters": {"type": "object", "properties": {}}},

            {"type": "function", "name": "above_stddev",
             "description": "Students above standard deviation",
             "parameters": {"type": "object", "properties": {}}},

            {"type": "function", "name": "below_stddev",
             "description": "Students below standard deviation",
             "parameters": {"type": "object", "properties": {}}},

            {"type": "function", "name": "completed_less_than",
             "description": "Students with completed assignments less than value",
             "parameters": {
                 "type": "object",
                 "properties": {"value": {"type": "integer"}},
                 "required": ["value"]
             }},

            {"type": "function", "name": "completed_under_percent",
             "description": "Students below percent completion",
             "parameters": {
                 "type": "object",
                 "properties": {"value": {"type": "number"}},
                 "required": ["value"]
             }},
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

    # -----------------------------
    # Extract Tool Call
    # -----------------------------

    tool_call = next(
        (item for item in response.output if item.type == "function_call"),
        None
    )

    if not tool_call:
        print("No tool call detected.")
        print(response.output_text)
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

    # -----------------------------
    # TOOL ROUTING
    # -----------------------------

    if tool_call.name == "student_count":
        tool_result = call_api("student_count")

    elif tool_call.name == "total_completed":
        tool_result = call_api("total_completed")

    elif tool_call.name == "expected_total":
        tool_result = call_api("expected_total")

    elif tool_call.name == "search_student":
        tool_result = call_api("student_search", name=args["name"])

    elif tool_call.name == "get_mean":
        tool_result = call_api("mean")

    elif tool_call.name == "get_stddev":
        tool_result = call_api("stddev")

    elif tool_call.name == "completed_all":
        tool_result = call_api("completed_all")

    elif tool_call.name == "above_stddev":
        tool_result = call_api("above_stddev")

    elif tool_call.name == "below_stddev":
        tool_result = call_api("below_stddev")

    elif tool_call.name == "completed_less_than":
        tool_result = call_api("completed_less_than", value=args["value"])

    elif tool_call.name == "completed_under_percent":
        tool_result = call_api("completed_under_percent", value=args["value"])

    else:
        print("Unknown tool:", tool_call.name)
        return

    log_step("TOOL RESULT (DATABASE)", tool_result)

    # -----------------------------
    # STEP 2 — Send Tool Output Back
    # -----------------------------

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