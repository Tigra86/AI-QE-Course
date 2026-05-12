import json
from openai import OpenAI
from jsonschema import Draft7Validator
from pathlib import Path

client = OpenAI()

SCHEMA_PATH = Path("schema2.json")
RAW_RESPONSE_PATH = Path("response_raw.json")

PROMPT = "What is the capital of France?"


def load_schema(path: Path) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def call_api(prompt: str) -> dict:
    response = client.responses.create(
        model="gpt-5.2",
        input=prompt,
        max_output_tokens=1000,
        temperature=0.7
    )

    response_dict = response.model_dump()

    RAW_RESPONSE_PATH.write_text(
        json.dumps(response_dict, indent=2),
        encoding="utf-8-sig"
    )

    return response_dict


def validate_all(instance: dict, schema: dict) -> None:
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)

    if not errors:
        print("Schema valid — no violations found")
        return

    print(f"{len(errors)} schema violations found:\n")

    for i, err in enumerate(errors, start=1):
        path = ".".join(map(str, err.absolute_path)) or "<root>"
        schema_path = ".".join(map(str, err.absolute_schema_path))

        print(f"{i}. Path: {path}")
        print(f"   Error: {err.message}")
        print(f"   Schema: {schema_path}\n")

    raise RuntimeError("Schema validation failed")


if __name__ == "__main__":
    schema = load_schema(SCHEMA_PATH)
    response_json = call_api(PROMPT)

    validate_all(response_json, schema)