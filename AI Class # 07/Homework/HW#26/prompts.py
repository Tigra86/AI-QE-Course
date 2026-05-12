import os
import json
from datetime import datetime
from openai import OpenAI

# -------------------------------------------------
# Configuration
# -------------------------------------------------
MODEL_NAME     = "gpt-4o-mini" #  gpt-3.5-turbo  gpt-4o-mini  gpt-5.2 
PROMPTS_FILE   = "prompts.json"
RESPONSES_FILE = "responses-" + MODEL_NAME + ".json"
# -------------------------------------------------
# OpenAI Client Call
# -------------------------------------------------
def call_openai(prompt: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()

# -------------------------------------------------
# Load Prompts (DICT with id + text)
# -------------------------------------------------
def load_prompts(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

# -------------------------------------------------
# Main Execution
# -------------------------------------------------
if __name__ == "__main__":
    PROMPTS = load_prompts(PROMPTS_FILE)
    results = []

    timestamp = datetime.now().strftime("%m-%d-%Y %I:%M:%S %p")

    print("=" * 80)
    print("PROMPT EXECUTION (OpenAI Only)\n")

    for name, item in PROMPTS.items():
        prompt_id   = item["id"]
        prompt_text = item["text"]

        print("-" * 80)
        print(f"NAME: {name}")
        print(f"ID:   {prompt_id}")
        print("PROMPT:")
        print(prompt_text)

        output = call_openai(prompt_text)

        print("\nMODEL OUTPUT:")
        print(output)

        results.append({
            "name": name,
            "id": prompt_id,
            "prompt": prompt_text,
            "prompt_output": output
        })

    # -------------------------------------------------
    # Write Results (with metadata envelope)
    # -------------------------------------------------
    final_output = {
        "timestamp": timestamp,
        "model": MODEL_NAME,
        "results": results
    }

    with open(RESPONSES_FILE, "w", encoding="utf-8-sig") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("Execution complete. Results written to " + RESPONSES_FILE)