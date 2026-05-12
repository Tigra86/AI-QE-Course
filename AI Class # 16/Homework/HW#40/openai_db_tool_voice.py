import sys
import json
import requests
import os
import sounddevice as sd
from scipy.io.wavfile import write
from datetime import datetime
from openai import OpenAI

# -----------------------------

API_URL = "https://alex.academy/ai/score/api.php"
MODEL = "gpt-5.2"

client = OpenAI()

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

def record_audio(seconds=6, fs=16000):

    os.makedirs("recordings", exist_ok=True)

    filename = f"recordings/question_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.wav"

    log_step("VOICE MODE", "Recording question...")

    audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype="float32")
    sd.wait()

    write(filename, fs, audio)

    log_step("AUDIO SAVED", filename)

    return filename

# -----------------------------

def transcribe_audio(file):

    log_step("TRANSCRIBE REQUEST", file)

    with open(file, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=f
        )

    log_step("TRANSCRIBE RESPONSE", transcript.text)

    return transcript.text

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

def main():

    if len(sys.argv) < 2:
        print("\nUsage:")
        print('python openai_db_tool_voice.py text "Question"')
        print("python openai_db_tool_voice.py voice")
        return

    mode = sys.argv[1].lower()

    # -----------------------------

    if mode == "text":

        if len(sys.argv) < 3:
            print('Usage: python openai_db_tool_voice.py text "Question"')
            return

        user_question = sys.argv[2]

    elif mode == "voice":

        audio_file = record_audio()
        user_question = transcribe_audio(audio_file)

    else:
        print("Mode must be 'text' or 'voice'")
        return


    log_step("USER QUESTION", user_question)

    response = client.responses.create(
        model=MODEL,
        tool_choice="required",
        input=[
            {
                "role": "system",
                "content": "You must answer database questions strictly by calling the most appropriate tool. Never answer from memory."
            },
            {
                "role": "user",
                "content": user_question
            }
        ],
        tools=[
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

    log_step("TOOL CALL DETECTED", args)

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

    log_step("STEP 2 FINAL RESPONSE", final_response.output)

    print("\nFINAL ANSWER:")
    print(final_response.output_text)


if __name__ == "__main__":
    main()
    