import json
from jsonschema import validate, ValidationError

RESPONSE_PATH = "response.json"
SCHEMA_PATH = "schema2.json"

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def validate_response(response_path: str, schema_path: str):
    response = load_json(response_path)
    schema = load_json(schema_path)

    try:
        validate(instance=response, schema=schema)
    except ValidationError as e:
        raise RuntimeError(
            f"Schema validation failed:\n{e.message}\n"
            f"At path: {'/'.join(map(str, e.absolute_path))}"
        ) from e

    print("Schema valid — no violations found")

if __name__ == "__main__":
    validate_response(RESPONSE_PATH, SCHEMA_PATH)