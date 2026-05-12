import os
from openai import OpenAI

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_FILE = "cases.txt"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MODEL_CONTEXT_WINDOWS = {
    "gpt-5.2":        128000,
    "gpt-5":          128000,
    "gpt-4.1-mini":   128000,
    "gpt-4.1":        128000,
    "gpt-4o":         128000,
    "gpt-5-nano":       8192,
    "gpt-4o-mini":      8192,
    "gpt-3.5-turbo":    4096
}

# -------------------------------------------------
# LOAD CASES
# -------------------------------------------------

def load_cases(path):
    with open(path, encoding="utf-8-sig") as f:
        lines = [l.strip() for l in f if l.strip()]

    header = lines[0].split("|")
    cases = []

    for line in lines[1:]:
        values = line.split("|", maxsplit=len(header) - 1)
        cases.append(dict(zip(header, values)))

    return cases

# -------------------------------------------------
# RUN SINGLE CASE
# -------------------------------------------------

def run_case(case):
    case_id     = case["id"]
    model       = case["model"]
    max_tokens  = int(case["max_token"])
    temperature = float(case["temperature"])
    prompt      = case["prompt"]

    response = client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=max_tokens,
        temperature=temperature
    )

    # -------------------------------
    # RAW RESPONSE DATA
    # -------------------------------
    status = response.output[0].status   # completed / incomplete
    text = (response.output_text or "").strip()

    input_tokens  = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    total_tokens  = response.usage.total_tokens  # billed tokens

    # -------------------------------
    # TOKEN ACCOUNTING
    # -------------------------------
    token_budget = MODEL_CONTEXT_WINDOWS.get(model)
    billed_tokens = total_tokens

    remaining_tokens = (
        token_budget - billed_tokens
        if token_budget is not None else None
    )

    available_for_output_at_start = (
        token_budget - input_tokens
        if token_budget is not None else None
    )

    if token_budget is None:
        limit_reason = "unknown"
    elif output_tokens >= available_for_output_at_start:
        limit_reason = "token_budget_exhausted"
    elif output_tokens >= max_tokens:
        limit_reason = "max_output_tokens"
    else:
        limit_reason = "none"

    # -------------------------------
    # AUTOMATIC TRUNCATION DETECTION
    # -------------------------------
    truncated = (status != "completed")

    # -------------------------------
    # WRITE OUTPUT FILE
    # -------------------------------
    filename = f"{case_id}_{model}_{status}_{max_tokens}_{temperature}.txt"
    path = os.path.join(OUTPUT_DIR, filename)

    with open(path, "w", encoding="utf-8-sig") as f:
        f.write("=== TOKEN ACCOUNTING ===\n")
        f.write(f"model: {model}\n")
        f.write(f"model_context_window / token_budget: {token_budget}\n")
        f.write(f"input_tokens: {input_tokens}\n")
        f.write(f"output_tokens: {output_tokens}\n")
        f.write(f"total_tokens / billed_tokens: {billed_tokens}\n")

        if remaining_tokens is not None:
            f.write(
                f"remaining_tokens / not_billed_tokens: "
                f"{remaining_tokens} ({token_budget} - {billed_tokens})\n"
            )
        else:
            f.write("remaining_tokens / not_billed_tokens: unknown\n")

        if available_for_output_at_start is not None:
            f.write(
                f"available_for_output_at_start: "
                f"{available_for_output_at_start}\n"
            )

        f.write(f"limit_reason: {limit_reason}\n")
        f.write(f"completion_status: {status}\n")
        f.write(f"truncated: {truncated}\n\n")

        f.write("=== PROMPT ===\n")
        f.write(prompt + "\n\n")

        f.write("=== RAW OUTPUT ===\n")
        f.write(text)

    print(f"Saved â†’ {path}")

# -------------------------------------------------
# MAIN
# -------------------------------------------------

if __name__ == "__main__":
    cases = load_cases(INPUT_FILE)

    for case in cases:
        run_case(case)