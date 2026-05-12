import requests
import json
import sys
import os
import sounddevice as sd
from scipy.io.wavfile import write
from datetime import datetime
from openai import OpenAI

# ---------------------------------------

MODEL = "gpt-5.2"
FX_API = "https://api.frankfurter.app/latest"

client = OpenAI()

# ---------------------------------------

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

def record_audio(seconds=6, fs=16000):

    os.makedirs("recordings", exist_ok=True)

    filename = f"recordings/question_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.wav"

    log_step("VOICE MODE", "Recording question...")

    audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype="float32")
    sd.wait()

    write(filename, fs, audio)

    log_step("AUDIO SAVED", filename)

    return filename

# ---------------------------------------

def transcribe_audio(file):

    log_step("TRANSCRIBE REQUEST", file)

    with open(file, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=f
        )

    log_step("TRANSCRIBE RESPONSE", transcript.text)

    return transcript.text

# ---------------------------------------

def convert_currency(amount, from_currency, to_currency):

    params = {
        "amount": amount,
        "from": from_currency.upper(),
        "to": to_currency.upper()
    }

    log_step("FX API REQUEST", params)

    response = requests.get(FX_API, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    if "rates" not in data or to_currency.upper() not in data["rates"]:
        raise ValueError("Invalid currency conversion")

    converted = round(data["rates"][to_currency.upper()], 2)

    result = {
        "amount": amount,
        "from_currency": from_currency.upper(),
        "to_currency": to_currency.upper(),
        "converted_amount": converted
    }

    log_step("FX API RESPONSE", result)

    return result

# ---------------------------------------

def main():

    if len(sys.argv) < 2:
        print("\nUsage:")
        print('python openai_currency_tool_voice.py text "Question"')
        print("python openai_currency_tool_voice.py voice")
        return

    mode = sys.argv[1].lower()

    # ------------------------------

    if mode == "text":

        if len(sys.argv) < 3:
            print('Usage: python openai_currency_tool_voice.py text "Question"')
            return

        user_question = sys.argv[2]

    # ------------------------------

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

    tool_result = convert_currency(
        args["amount"],
        args["from_currency"],
        args["to_currency"]
    )

    log_step("TOOL EXECUTION RESULT", tool_result)

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
    