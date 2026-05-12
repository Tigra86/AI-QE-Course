import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from jsonschema import validate, ValidationError

client = OpenAI()

ENVELOPE_SCHEMA_PATH = "schema.json"

PROMPT = "What is the capital of France?"

def load_schema(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def validate_and_store_response(prompt: str, schema_path: str):
    response = client.responses.create(
        model="gpt-5.2",
        input=prompt,
        max_output_tokens=1000,
        temperature=0.7
    )

    response_dict = response.model_dump()

    schema = load_schema(schema_path)
    try:
        validate(instance=response_dict, schema=schema)
    except ValidationError as e:
        raise RuntimeError(
            f"Envelope schema validation failed:\n{e.message}"
        ) from e

    ts = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")

    filename = f"response_{ts}.json"

    with open(filename, "w", encoding="utf-8-sig") as f:
        json.dump(response_dict, f, indent=2, ensure_ascii=False)

    return filename

if __name__ == "__main__":
    path = validate_and_store_response(PROMPT,ENVELOPE_SCHEMA_PATH)
    print("Schema valid")
    print("Response stored at:", path)
