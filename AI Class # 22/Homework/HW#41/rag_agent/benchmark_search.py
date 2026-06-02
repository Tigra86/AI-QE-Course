from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import matplotlib.pyplot as plt

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

STORE_DIR = Path("rag_store")
VECTORS_PATH = STORE_DIR / "openai_vectors.npy"
META_PATH = STORE_DIR / "openai_metadata.json"

OUTPUT_DIR = Path("benchmark_output")
CSV_PATH = OUTPUT_DIR / "benchmark_results.csv"
CHART_PATH = OUTPUT_DIR / "benchmark_chart.png"

TOP_K = 4
RUNS = 2000
REPEAT_FACTORS = [1, 100, 1000, 5000]

@dataclass
class ChunkRecord:
    chunk_id: str
    source_file: str
    chunk_index: int
    text: str

def load_vectors_and_metadata() -> Tuple[np.ndarray, List[ChunkRecord]]:
    vectors = np.load(VECTORS_PATH).astype("float32")
    raw = json.loads(META_PATH.read_text(encoding="utf-8"))
    metadata = [ChunkRecord(**item) for item in raw]
    return vectors, metadata

def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    return vectors / norms

def make_query_from_doc(vectors: np.ndarray, doc_idx: int = 0) -> np.ndarray:
    query_vec = vectors[doc_idx:doc_idx + 1].copy().astype("float32")
    return l2_normalize(query_vec)

def repeat_vectors(
    vectors: np.ndarray,
    metadata: List[ChunkRecord],
    repeats: int,
) -> Tuple[np.ndarray, List[ChunkRecord]]:
    big_vectors = np.tile(vectors, (repeats, 1)).astype("float32")

    big_metadata: List[ChunkRecord] = []
    for r in range(repeats):
        for item in metadata:
            big_metadata.append(
                ChunkRecord(
                    chunk_id=f"{item.chunk_id}__copy_{r}",
                    source_file=item.source_file,
                    chunk_index=item.chunk_index,
                    text=item.text,
                )
            )
    return big_vectors, big_metadata

def brute_force_search(query_vec: np.ndarray, doc_vectors: np.ndarray, top_k: int = TOP_K):
    scores = np.dot(doc_vectors, query_vec.T).flatten()
    top_indices = np.argsort(-scores)[:top_k]
    return [(float(scores[i]), int(i)) for i in top_indices]

def build_flat_index(vectors: np.ndarray):
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors.astype("float32"))
    return index

def build_hnsw_index(vectors: np.ndarray, m: int = 32, ef_construction: int = 200):
    dim = vectors.shape[1]
    index = faiss.IndexHNSWFlat(dim, m)
    index.hnsw.efConstruction = ef_construction
    index.add(vectors.astype("float32"))
    return index

def faiss_search(query_vec: np.ndarray, index, top_k: int = TOP_K):
    scores, indices = index.search(query_vec.astype("float32"), top_k)
    return [(float(scores[0][i]), int(indices[0][i])) for i in range(top_k)]

def benchmark(fn, runs: int = RUNS) -> float:
    start = time.perf_counter()
    for _ in range(runs):
        fn()
    return time.perf_counter() - start

def run_case(vectors: np.ndarray, label: str) -> dict:
    query_vec = make_query_from_doc(vectors, doc_idx=0)

    bf_time = benchmark(lambda: brute_force_search(query_vec, vectors, TOP_K), RUNS)

    flat_time = None
    hnsw_time = None

    if FAISS_AVAILABLE:
        flat_index = build_flat_index(vectors)
        hnsw_index = build_hnsw_index(vectors)

        hnsw_index.hnsw.efSearch = 64

        flat_time = benchmark(lambda: faiss_search(query_vec, flat_index, TOP_K), RUNS)
        hnsw_time = benchmark(lambda: faiss_search(query_vec, hnsw_index, TOP_K), RUNS)

    return {
        "label": label,
        "corpus_size": len(vectors),
        "runs": RUNS,
        "bruteforce_avg_ms": bf_time / RUNS * 1000,
        "flat_avg_ms": flat_time / RUNS * 1000 if flat_time is not None else None,
        "hnsw_avg_ms": hnsw_time / RUNS * 1000 if hnsw_time is not None else None,
    }

def save_csv(rows: List[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "label",
                "corpus_size",
                "runs",
                "bruteforce_avg_ms",
                "flat_avg_ms",
                "hnsw_avg_ms",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

def save_chart(rows: List[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    labels = [r["label"] for r in rows]
    bf = [r["bruteforce_avg_ms"] for r in rows]
    flat = [r["flat_avg_ms"] if r["flat_avg_ms"] is not None else 0 for r in rows]
    hnsw = [r["hnsw_avg_ms"] if r["hnsw_avg_ms"] is not None else 0 for r in rows]

    x = np.arange(len(labels))
    width = 0.25

    plt.figure(figsize=(11, 6))
    plt.bar(x - width, bf, width, label="Brute-force")
    plt.bar(x, flat, width, label="FAISS Flat")
    plt.bar(x + width, hnsw, width, label="FAISS HNSW")

    plt.xlabel("Corpus Scale")
    plt.ylabel("Average Retrieval Time (ms/query)")
    plt.title("Retrieval Speed: Brute-force vs FAISS Flat vs FAISS HNSW")
    plt.xticks(x, labels)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

def main():
    vectors, metadata = load_vectors_and_metadata()
    rows: List[dict] = []

    print(f"FAISS available: {FAISS_AVAILABLE}")
    print(f"Base chunks: {len(vectors):,}")
    print(f"Dim: {vectors.shape[1]}")

    for repeats in REPEAT_FACTORS:
        scaled_vectors, _ = repeat_vectors(vectors, metadata, repeats)
        label = "original" if repeats == 1 else f"x{repeats:,}"
        row = run_case(scaled_vectors, label)
        rows.append(row)

        print(f"\n{label} ({row['corpus_size']:,} chunks)")
        print(f"  Brute-force: {row['bruteforce_avg_ms']:.6f} ms/query")
        if row["flat_avg_ms"] is not None:
            print(f"  FAISS Flat:  {row['flat_avg_ms']:.6f} ms/query")
            print(f"  FAISS HNSW:  {row['hnsw_avg_ms']:.6f} ms/query")

    save_csv(rows, CSV_PATH)
    save_chart(rows, CHART_PATH)

    print(f"\nCSV:   {CSV_PATH.resolve()}")
    print(f"Chart: {CHART_PATH.resolve()}")

if __name__ == "__main__":
    main()
    