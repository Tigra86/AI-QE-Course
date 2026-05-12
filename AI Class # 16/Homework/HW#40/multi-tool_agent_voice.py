# pip install openai requests sounddevice scipy

import platform
import os
import json
import math
import time
import requests
import sounddevice as sd
from scipy.io.wavfile import write
from datetime import datetime
from uuid import uuid4
from openai import OpenAI

client = OpenAI()

MODEL = "gpt-5.2"

WEATHER_API = "https://api.open-meteo.com/v1/forecast"
GEO_API = "https://nominatim.openstreetmap.org/search"
FX_API = "https://api.frankfurter.app/latest"
DB_API = "https://alex.academy/ai/score/api.php"

os.makedirs("questions", exist_ok=True)
os.makedirs("answers", exist_ok=True)

# ------------------------------------------------

def generate_timestamp():
    return datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")

def record_audio(qid):

    fs = 16000
    seconds = 6

    filename = f"questions/{qid}.wav"

    print("\nSpeak now...")

    audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype="float32")
    sd.wait()

    write(filename, fs, audio)

    return filename

def transcribe_audio(file):

    with open(file, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=f
        )

    return transcript.text

def rename_question_audio(qid, tool):

    old_file = f"questions/{qid}.wav"
    new_file = f"questions/{tool}_{qid}.wav"

    if os.path.exists(old_file):
        os.rename(old_file, new_file)

def play_audio(file):

    system = platform.system()

    if system == "Darwin":
        os.system(f"afplay {file}")

    elif system == "Windows":
        import winsound
        winsound.PlaySound(file, winsound.SND_FILENAME)

    else:
        os.system(f"aplay {file}")

def speak(text, qid, tool):

    speech = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    )

    filename = f"answers/{tool}_{qid}.wav"

    with open(filename, "wb") as f:
        f.write(speech.read())

    play_audio(filename)

# ------------------------------------------------

def save_question(qid, tool, question):

    filename = f"questions/{tool}_{qid}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(question)


def save_answer(qid, tool, answer):

    filename = f"answers/{tool}_{qid}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(answer)

# ------------------------------------------------

def get_lat_lon(city):
    time.sleep(1)
    r = requests.get(
        GEO_API,
        params={"q": city, "format": "json", "limit": 1},
        headers={"User-Agent": "ai-agent"},
        timeout=10
    )

    data = r.json()

    if not data:
        raise ValueError("Location not found")
    return float(data[0]["lat"]), float(data[0]["lon"])

def get_weather(city, unit="C"):

    unit_api = "fahrenheit" if unit == "F" else "celsius"
    lat, lon = get_lat_lon(city)

    r = requests.get(
        WEATHER_API,
        params={"latitude": lat, "longitude": lon, "current_weather": True, "temperature_unit": unit_api},
        timeout=10
    )

    data = r.json()

    return {
        "city": city,
        "temperature": data["current_weather"]["temperature"],
        "unit": unit
    }

# ------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):

    R = 6371

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi/2)**2 +
        math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R*c


def calculate_distance(origin, destination):

    lat1, lon1 = get_lat_lon(origin)
    lat2, lon2 = get_lat_lon(destination)

    km = haversine(lat1, lon1, lat2, lon2)

    return {
        "origin": origin,
        "destination": destination,
        "distance_km": round(km,2)
    }

# ------------------------------------------------

def convert_currency(amount, from_currency, to_currency):

    r = requests.get(
        FX_API,
        params={
            "amount": amount,
            "from": from_currency,
            "to": to_currency
        },
        timeout=10
    )

    data = r.json()

    return {
        "amount": amount,
        "from": from_currency,
        "to": to_currency,
        "converted": data["rates"][to_currency]
    }

# ------------------------------------------------

def database_query(action, name=None, value=None):

    action_map = {
        "student_count": "student_count",
        "total_completed": "total_completed",
        "expected_total": "expected_total",
        "search_student": "student_search",
        "mean": "mean",
        "stddev": "stddev",
        "completed_all": "completed_all",
        "above_stddev": "above_stddev",
        "below_stddev": "below_stddev",
        "completed_less_than": "completed_less_than",
        "completed_under_percent": "completed_under_percent"
    }

    api_action = action_map.get(action)

    if not api_action:
        raise ValueError(f"Invalid action: {action}")

    params = {"action": api_action}

    if name:
        params["name"] = name

    if value is not None:
        params["value"] = value

    # print("\nDATABASE REQUEST:", params)

    r = requests.get(DB_API, params=params, timeout=10)

    return r.json()

# ------------------------------------------------

def run_agent(question):

    response = client.responses.create(

        model=MODEL,
        tool_choice="required",

        input=[
            {
            "role": "system",
            "content": """
            You are an AI assistant connected to tools.
            You MUST answer student database questions using database_query.

            Examples:
            How many students are there? → student_count
            How many assignments did Yuri → search_student with name="Yuri"
            Who completed all assignments? → completed_all
            Who completed less than 5 assignments? → completed_less_than value=5
            Who is below 50 percent completion? → completed_under_percent value=50

            Never invent actions.
            Only use the provided enum values.
            """
            },
            {
                "role": "user",
                "content": question
            }
        ],

        tools=[

            {
                "type": "function",
                "name": "get_weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city":{"type":"string"},
                        "unit":{"type":"string"}
                    },
                    "required":["city"]
                }
            },

            {
                "type":"function",
                "name":"calculate_distance",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "origin":{"type":"string"},
                        "destination":{"type":"string"}
                    },
                    "required":["origin","destination"]
                }
            },

            {
                "type":"function",
                "name":"convert_currency",
                "parameters":{
                    "type":"object",
                    "properties":{
                        "amount":{"type":"number"},
                        "from_currency":{"type":"string"},
                        "to_currency":{"type":"string"}
                    },
                    "required":["amount","from_currency","to_currency"]
                }
            },

            {
                "type": "function",
                "name": "database_query",
                "description": """
                Query the student assignment database.

                Use the following actions:

                student_count → total number of students
                total_completed → total assignments completed by all students
                expected_total → expected assignments (students × assignments)
                search_student → find a student by name (requires 'name')
                mean → average assignments completed
                stddev → standard deviation of assignments completed
                completed_all → students who completed all assignments
                above_stddev → students above standard deviation
                below_stddev → students below standard deviation
                completed_less_than → students with completed assignments < value
                completed_under_percent → students below completion percent

                Always choose the closest matching action.
                """,
                "parameters": {
                "type": "object",
                "properties": {

                "action": {
                "type": "string",
                "enum": [
                        "student_count",
                        "total_completed",
                        "expected_total",
                        "search_student",
                        "mean",
                        "stddev",
                        "completed_all",
                        "above_stddev",
                        "below_stddev",
                        "completed_less_than",
                        "completed_under_percent"
                        ]
                },

                "name": {
                "type": "string",
                "description": "Student name for search_student action"
                },

                "value": {
                "type": "number",
                "description": "Numeric threshold for filtering"
                }

                },
                "required": ["action"]
                }
            }

        ]
    )

    tool_call = next(
        (i for i in response.output if i.type=="function_call"), None)

    if not tool_call:
        return response.output_text, "llm"

    args = tool_call.arguments

    if isinstance(args,str):
        args=json.loads(args)

    print("\nTool:",tool_call.name)

    if tool_call.name=="get_weather":
        result=get_weather(**args)

    elif tool_call.name=="calculate_distance":
        result=calculate_distance(**args)

    elif tool_call.name=="convert_currency":
        result=convert_currency(**args)

    elif tool_call.name=="database_query":
        result=database_query(**args)

    else:
        return "Unknown tool","error"

    final = client.responses.create(

        model=MODEL,
        previous_response_id=response.id,

        input=[{
            "type":"function_call_output",
            "call_id":tool_call.call_id,
            "output":json.dumps(result)
        }]
    )

    return final.output_text, tool_call.name

# ------------------------------------------------

stop_words=["exit","stop","quit"]

while True:

    qid = generate_timestamp()
    audio_file = record_audio(qid)
    question = transcribe_audio(audio_file)

    print("\nQuestion:",question)

    if any(word in question.lower() for word in stop_words):
        print("Assistant stopped.")
        break

    answer,tool = run_agent(question)

    print("\nAnswer:",answer)
    rename_question_audio(qid, tool)
    save_question(qid,tool,question)
    save_answer(qid,tool,answer)
    speak(answer,qid,tool)
