import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from jsonschema import validate, ValidationError

client = OpenAI()

# Updated prompt to ask about the 2023 Stanley Cup winner
PROMPT = "Who won the Stanley Cup in 2023?"

def store_response(prompt: str):
    response = client.responses.create(
        model="gpt-5.2",
        input=prompt,
        max_output_tokens=1000,
        temperature=0.7
    )

    response_dict = response.model_dump()

    ts = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")

    filename = f"response_{ts}.json"

    with open(filename, "w", encoding="utf-8-sig") as f:
        json.dump(response_dict, f, indent=2, ensure_ascii=False)

    return filename

if __name__ == "__main__":
    path = store_response(PROMPT)
    print("Response stored at:", path)