# python performance_test.py "Who completed all assignments?" 3
# python performance_test.py "Students with completed assignments under 20?" 3
# python performance_test.py "How many students do we have?" 3

import sys
import json
import time
import math
import statistics
from datetime import datetime
from openai import OpenAI

# ---------------- CONFIG ----------------
MODEL = "gpt-5.2"
RESULTS_FILE = "performance_results.json"
DEFAULT_RUNS = 1
SLA_THRESHOLD = 7.0

client = OpenAI()


# ---------------- Percentile ----------------
def percentile(data, p):
    if not data:
        return 0.0
    data = sorted(data)
    k = (len(data) - 1) * (p / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data[int(k)]
    return data[f] * (c - k) + data[c] * (k - f)


# ---------------- Trimmed Mean ----------------
def trimmed_mean(data, trim_percent=5):
    if not data:
        return 0.0
    data = sorted(data)
    n = len(data)
    trim = int(n * trim_percent / 100)
    if n <= trim * 2:
        return statistics.mean(data)
    return statistics.mean(data[trim:n - trim])


# ---------------- Compute Metrics ----------------
def compute_metrics(latencies, errors):
    total_runs = len(latencies)

    if total_runs == 0:
        return {}

    mean_val = statistics.mean(latencies)
    std_val = statistics.stdev(latencies) if total_runs > 1 else 0.0

    sla_passes = len([x for x in latencies if x <= SLA_THRESHOLD])

    return {
        "total_runs": total_runs,
        "average": round(mean_val, 3),
        "p50": round(percentile(latencies, 50), 3),
        "p95": round(percentile(latencies, 95), 3),
        "p99": round(percentile(latencies, 99), 3),
        "trimmed_mean_5": round(trimmed_mean(latencies), 3),
        "min": round(min(latencies), 3),
        "max": round(max(latencies), 3),
        "std_dev": round(std_val, 3),
        "error_rate_pct": round((errors / total_runs) * 100, 3),
        "sla_pass_rate_pct": round((sla_passes / total_runs) * 100, 3),
        "sla_threshold": SLA_THRESHOLD
    }


# ---------------- Save Results ----------------
def save_results(entry):
    try:
        with open(RESULTS_FILE, "r") as f:
            history = json.load(f)
    except:
        history = []

    history.append(entry)

    with open(RESULTS_FILE, "w") as f:
        json.dump(history, f, indent=2)


# ---------------- Main ----------------
def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print('python performance_e2e_test.py "Question" [iterations]')
        return

    question = sys.argv[1]
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_RUNS

    print(f"\n=== PERFORMANCE TEST ({runs} runs) ===\n")

    step1_times = []
    tool_times = []
    step2_times = []
    total_times = []
    errors = 0

    for i in range(runs):
        try:
            t0 = time.perf_counter()

            # STEP 1
            s1 = time.perf_counter()
            response = client.responses.create(
                model=MODEL,
                input=question
            )
            step1 = time.perf_counter() - s1

            # TOOL (simulate)
            s_tool = time.perf_counter()
            time.sleep(0.5)
            tool = time.perf_counter() - s_tool

            # STEP 2
            s2 = time.perf_counter()
            client.responses.create(
                model=MODEL,
                previous_response_id=response.id,
                input="OK"
            )
            step2 = time.perf_counter() - s2

            total = time.perf_counter() - t0

            step1_times.append(step1)
            tool_times.append(tool)
            step2_times.append(step2)
            total_times.append(total)

            print(
                f"Iteration {i+1}: "
                f"S1={step1:.3f}s | "
                f"Tool={tool:.3f}s | "
                f"S2={step2:.3f}s | "
                f"Total={total:.3f}s"
            )

        except Exception as e:
            errors += 1
            print(f"Iteration {i+1}: ERROR → {e}")

    print("\n=== SUMMARY ===")

    metrics = {
        "llm_step1": compute_metrics(step1_times, errors),
        "tool": compute_metrics(tool_times, errors),
        "llm_step2": compute_metrics(step2_times, errors),
        "total": compute_metrics(total_times, errors)
    }

    for section, values in metrics.items():
        print(f"\n--- {section.upper()} ---")
        for k, v in values.items():
            print(f"{k}: {v}")

    save_results({
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "runs": runs,
        "metrics": metrics
    })

    print("\nResults saved to performance_results.json")


if __name__ == "__main__":
    main()
