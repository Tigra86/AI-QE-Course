import csv
import json
import math
import random
import datetime
from html import escape

# ============================================================
# Configuration
# ============================================================
CSV_PATH = "sentences.csv"
JSONL_PATH = "candidates.jsonl"
OUTPUT_HTML = "decoding_report.html"

SEED = 42
SAMPLES = 5
TEMPERATURES = (0.0, 0.7, 1.5)
TOP_K = 2
TOP_P = 0.70

STRATEGY_COLORS = {
    "Greedy": "#1f77b4",
    "Random": "#ff7f0e",
    "Temperature": "#2ca02c",
    "Top-K": "#9467bd",
    "Top-P": "#d62728",
}

# ============================================================
# Data loading
# ============================================================
def load_sentences(path):
    data = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=";"):
            data[int(row["id"])] = row["text"]
    return data


def load_logits(path):
    data = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            assert "id" in obj and "logits" in obj
            data[int(obj["id"])] = obj["logits"]
    return data


# ============================================================
# Core math
# ============================================================
def apply_temperature(logits, temperature):
    if temperature == 0.0:
        return logits
    return {k: v / temperature for k, v in logits.items()}


def softmax(logits):
    m = max(logits.values())
    exps = {k: math.exp(v - m) for k, v in logits.items()}
    total = sum(exps.values())
    return {k: v / total for k, v in exps.items()}


# ============================================================
# Decoding
# ============================================================
def greedy_from_logits(logits):
    return max(logits, key=logits.get)


def random_sampling(probs):
    return random.choices(list(probs.keys()), list(probs.values()), k=1)[0]


def top_k_deterministic(logits, k):
    return [
        w for w, _ in sorted(
            logits.items(),
            key=lambda x: x[1],
            reverse=True
        )[:k]
    ]


def top_p_deterministic(logits, p):
    probs = softmax(logits)
    sorted_items = sorted(probs.items(), key=lambda x: x[1], reverse=True)

    nucleus = []
    cumulative = 0.0
    for w, prob in sorted_items:
        nucleus.append(w)
        cumulative += prob
        if cumulative >= p:
            break
    return nucleus


def decode_temperature_sample(logits, temperature):
    if temperature == 0.0:
        return greedy_from_logits(logits)
    probs = softmax(apply_temperature(logits, temperature))
    return random_sampling(probs)


def get_probability_for_word(logits, temperature, word, base_probs):
    if temperature == 0.0:
        return base_probs[word]
    return softmax(apply_temperature(logits, temperature))[word]


# ============================================================
# HTML helpers
# ============================================================
def fill_highlight(template, word, prob, color):
    token = (
        f'<span class="token" style="color:{color}" '
        f'title="p={prob:.3f}">{escape(word)}</span>'
    )
    return escape(template).replace("||", token)


# ============================================================
# HTML rendering
# ============================================================
def render_html(results):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='utf-8'>",
        "<title>LLM Decoding Report</title>",
        "</head><body>",
        "<h1>LLM Decoding Strategies Report</h1>",
        f"<div>Generated at {now}</div>",
    ]

    for sid, block in results.items():
        html.append("<hr>")
        html.append(f"<h2>Sentence ID {sid}</h2>")
        html.append(f"<div>{block['template']}</div>")
        html.append("<ul>")

        for _, name, lines in block["rows"]:
            html.append(f"<li><strong>{name}</strong>")
            for i, s in enumerate(lines, 1):
                html.append(f"<div>{i}. {s}</div>")
            html.append("</li>")

        html.append("</ul>")

    html.append("</body></html>")

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write("\n".join(html))


# ============================================================
# Main
# ============================================================
def main():
    random.seed(SEED)

    sentences = load_sentences(CSV_PATH)
    logits_data = load_logits(JSONL_PATH)

    results = {}

    for sid, template in sentences.items():
        logits = logits_data[sid]
        probs = softmax(logits)

        rows = []

        # Greedy
        g = greedy_from_logits(logits)
        rows.append(("greedy", "Greedy", [
            fill_highlight(template, g, probs[g], STRATEGY_COLORS["Greedy"])
        ] * SAMPLES))

        # Random
        rows.append(("random", "Random Sampling", [
            fill_highlight(template, (w := random_sampling(probs)), probs[w], STRATEGY_COLORS["Random"])
            for _ in range(SAMPLES)
        ]))

        # Temperature
        for T in TEMPERATURES:
            rows.append(("temp", f"Temperature (T={T})", [
                fill_highlight(
                    template,
                    (w := decode_temperature_sample(logits, T)),
                    get_probability_for_word(logits, T, w, probs),
                    STRATEGY_COLORS["Temperature"]
                )
                for _ in range(SAMPLES)
            ]))

        # Top-K Deterministic
        rows.append(("topk", f"Top-K Deterministic (K={TOP_K})", [
            fill_highlight(template, w, probs[w], STRATEGY_COLORS["Top-K"])
            for w in top_k_deterministic(logits, TOP_K)
        ]))

        # Top-P Deterministic
        rows.append(("topp", f"Top-P Deterministic (P={TOP_P})", [
            fill_highlight(template, w, probs[w], STRATEGY_COLORS["Top-P"])
            for w in top_p_deterministic(logits, TOP_P)
        ]))

        results[sid] = {
            "template": escape(template),
            "rows": rows
        }

    render_html(results)


if __name__ == "__main__":
    main()
    