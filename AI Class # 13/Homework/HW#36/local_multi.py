import json
from jsonschema import Draft7Validator
from pathlib import Path


RESPONSE_PATH = Path("response.json")
SCHEMA_PATH = Path("schema2.json")


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


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
    response = load_json(RESPONSE_PATH)
    schema = load_json(SCHEMA_PATH)

    validate_all(response, schema)