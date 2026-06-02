from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("Missing OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"
GENERATION_MODEL = "gpt-5.2"

KB_DIR = Path("knowledge_base")
STORE_DIR = Path("rag_store")

FLAT_INDEX_PATH = STORE_DIR / "openai_faiss_flat.index"
HNSW_INDEX_PATH = STORE_DIR / "openai_faiss_hnsw.index"
VECTORS_PATH = STORE_DIR / "openai_vectors.npy"
META_PATH = STORE_DIR / "openai_metadata.json"

CHUNK_SIZE = 700
CHUNK_OVERLAP = 120
EMBED_BATCH_SIZE = 64
TOP_K = 4

@dataclass
class ChunkRecord:
    chunk_id: str
    source_file: str
    chunk_index: int
    text: str

def load_documents(folder: Path) -> List[Tuple[str, str]]:
    docs: List[Tuple[str, str]] = []

    if not folder.exists():
        raise FileNotFoundError(f"Knowledge base folder not found: {folder}")

    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                docs.append((path.name, text))

    if not docs:
        raise ValueError(f"No supported documents found in {folder}")

    return docs

def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = normalize_whitespace(text)
    if not text:
        return []

    chunks: List[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(start + 1, end - overlap)

    return chunks

def build_chunk_records(folder: Path) -> List[ChunkRecord]:
    records: List[ChunkRecord] = []

    for source_file, doc_text in load_documents(folder):
        chunks = chunk_text(doc_text, CHUNK_SIZE, CHUNK_OVERLAP)
        for i, chunk in enumerate(chunks):
            records.append(
                ChunkRecord(
                    chunk_id=f"{source_file}::chunk_{i}",
                    source_file=source_file,
                    chunk_index=i,
                    text=chunk,
                )
            )
    return records

def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    return vectors / norms

def embed_texts(texts: List[str], model: str = EMBEDDING_MODEL) -> np.ndarray:
    all_vectors: List[List[float]] = []

    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i:i + EMBED_BATCH_SIZE]

        response = client.embeddings.create(
            model=model,
            input=batch,
        )

        batch_vectors = [item.embedding for item in response.data]
        all_vectors.extend(batch_vectors)

    vectors = np.array(all_vectors, dtype="float32")
    vectors = l2_normalize(vectors)
    return vectors

def embed_query(query: str) -> np.ndarray:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
    )
    vec = np.array([response.data[0].embedding], dtype="float32")
    vec = l2_normalize(vec)
    return vec

def build_faiss_index_hnsw(
    vectors: np.ndarray,
    m: int = 32,
    ef_construction: int = 200,
):
    if not FAISS_AVAILABLE:
        raise RuntimeError("FAISS is not installed.")

    dim = vectors.shape[1]
    index = faiss.IndexHNSWFlat(dim, m, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = ef_construction
    index.add(vectors.astype("float32"))
    return index

def build_faiss_index_flat(vectors: np.ndarray):
    if not FAISS_AVAILABLE:
        raise RuntimeError(
            "FAISS is not installed. Use pip install faiss-cpu"
        )

    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors.astype("float32"))
    return index

def save_store(
    flat_index,
    hnsw_index,
    vectors: np.ndarray,
    metadata: List[ChunkRecord],
) -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)

    if flat_index is not None:
        faiss.write_index(flat_index, str(FLAT_INDEX_PATH))

    if hnsw_index is not None:
        faiss.write_index(hnsw_index, str(HNSW_INDEX_PATH))

    np.save(VECTORS_PATH, vectors)

    payload = [asdict(record) for record in metadata]
    META_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def load_store() -> Tuple[Any, Any, np.ndarray, List[ChunkRecord]]:
    if not VECTORS_PATH.exists():
        raise FileNotFoundError(f"Missing vectors file: {VECTORS_PATH}")
    if not META_PATH.exists():
        raise FileNotFoundError(f"Missing metadata file: {META_PATH}")

    flat_index = None
    hnsw_index = None

    if FAISS_AVAILABLE and FLAT_INDEX_PATH.exists():
        flat_index = faiss.read_index(str(FLAT_INDEX_PATH))

    if FAISS_AVAILABLE and HNSW_INDEX_PATH.exists():
        hnsw_index = faiss.read_index(str(HNSW_INDEX_PATH))

    vectors = np.load(VECTORS_PATH)
    raw = json.loads(META_PATH.read_text(encoding="utf-8"))
    metadata = [ChunkRecord(**item) for item in raw]

    return flat_index, hnsw_index, vectors, metadata

def rebuild_knowledge_base() -> None:
    print("Building chunk records...")
    records = build_chunk_records(KB_DIR)
    print(f"Loaded {len(records)} chunks.")
    print("Embedding chunks...")
    vectors = embed_texts([r.text for r in records], model=EMBEDDING_MODEL)

    flat_index = None
    hnsw_index = None

    if FAISS_AVAILABLE:
        print("Building FAISS Flat index...")
        flat_index = build_faiss_index_flat(vectors)

        print("Building FAISS HNSW index...")
        hnsw_index = build_faiss_index_hnsw(vectors)
    else:
        print("FAISS not installed.")

    print("Saving store...")
    save_store(flat_index, hnsw_index, vectors, records)

    print(f"Done. Saved to: {STORE_DIR.resolve()}")

def search_index_hnsw(
    query: str,
    index,
    metadata: List[ChunkRecord],
    top_k: int = TOP_K,
    ef_search: int = 64,
) -> List[Dict[str, Any]]:
    if not FAISS_AVAILABLE:
        raise RuntimeError("FAISS is not installed.")
    if index is None:
        raise RuntimeError("FAISS index is missing. Run: python openai_rag_agent.py build")

    query_vec = embed_query(query)
    index.hnsw.efSearch = ef_search

    scores, indices = index.search(query_vec.astype("float32"), top_k)

    results: List[Dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        record = metadata[int(idx)]
        results.append(
            {
                "score": float(score),
                "chunk_id": record.chunk_id,
                "source_file": record.source_file,
                "chunk_index": record.chunk_index,
                "text": record.text,
            }
        )

    return results

def search_index_faiss(
    query: str,
    index,
    metadata: List[ChunkRecord],
    top_k: int = TOP_K,
) -> List[Dict[str, Any]]:
    if not FAISS_AVAILABLE:
        raise RuntimeError("FAISS mode requested, but FAISS is not installed.")
    if index is None:
        raise RuntimeError("FAISS index is missing. Run: python openai_rag_agent.py build")

    query_vec = embed_query(query)
    scores, indices = index.search(query_vec.astype("float32"), top_k)

    results: List[Dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        record = metadata[int(idx)]
        results.append(
            {
                "score": float(score),
                "chunk_id": record.chunk_id,
                "source_file": record.source_file,
                "chunk_index": record.chunk_index,
                "text": record.text,
            }
        )

    return results

def search_index_bruteforce(
    query: str,
    vectors: np.ndarray,
    metadata: List[ChunkRecord],
    top_k: int = TOP_K,
) -> List[Dict[str, Any]]:
    query_vec = embed_query(query)
    scores = np.dot(vectors, query_vec.T).flatten()
    top_indices = np.argsort(-scores)[:top_k]
    results: List[Dict[str, Any]] = []
    for idx in top_indices:
        record = metadata[int(idx)]
        results.append(
            {
                "score": float(scores[idx]),
                "chunk_id": record.chunk_id,
                "source_file": record.source_file,
                "chunk_index": record.chunk_index,
                "text": record.text,
            }
        )

    return results

def build_context_block(results: List[Dict[str, Any]]) -> str:
    lines: List[str] = []

    for i, item in enumerate(results, start=1):
        lines.append(
            f"[Source {i}] file={item['source_file']} "
            f"chunk={item['chunk_index']} score={item['score']:.4f}\n"
            f"{item['text']}\n"
        )

    return "\n".join(lines).strip()

def answer_with_rag(
    user_question: str,
    top_k: int = TOP_K,
    mode: str = "faiss",
) -> Dict[str, Any]:
    flat_index, hnsw_index, vectors, metadata = load_store()

    if mode == "faiss":
        retrieved = search_index_faiss(user_question, flat_index, metadata, top_k=top_k)
    elif mode == "hnsw":
        retrieved = search_index_hnsw(user_question, hnsw_index, metadata, top_k=top_k)
    elif mode == "bruteforce":
        retrieved = search_index_bruteforce(user_question, vectors, metadata, top_k=top_k)
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    context_block = build_context_block(retrieved)

    system_prompt = (
        "You are a retrieval-augmented assistant.\n"
        "Answer the user's question using the retrieved context when relevant.\n"
        "If the answer is not supported by the retrieved context, say that the retrieved context does not fully support it.\n"
        "Cite sources inline as [Source N] where appropriate.\n"
        "Do not invent source contents."
    )

    user_prompt = (
        f"User question:\n{user_question}\n\n"
        f"Retrieved context:\n{context_block}\n\n"
        "Produce a concise but accurate answer with inline citations."
    )

    response = client.responses.create(
        model=GENERATION_MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return {
        "question": user_question,
        "retrieved": retrieved,
        "answer": response.output_text.strip(),
    }

def print_results(payload: Dict[str, Any]) -> None:
    print("\n" + "=" * 80)
    print("QUESTION")
    print("=" * 80)
    print(payload["question"])
    print("\n" + "=" * 80)
    print("RETRIEVED CHUNKS")
    print("=" * 80)
    for i, item in enumerate(payload["retrieved"], start=1):
        print(
            f"\n[Source {i}] score={item['score']:.4f} "
            f"file={item['source_file']} chunk={item['chunk_index']}"
        )
        print(item["text"][:500] + ("..." if len(item["text"]) > 500 else ""))

    print("\n" + "=" * 80)
    print("FINAL ANSWER")
    print("=" * 80)
    print(payload["answer"])

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="RAG Agent with FAISS or brute-force retrieval"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="Build or rebuild vectors and FAISS index")
    ask_parser = subparsers.add_parser("ask", help="Ask a question using RAG")
    ask_parser.add_argument("question", type=str, help="Question to ask")
    ask_parser.add_argument(
        "--top-k",
        type=int,
        default=TOP_K,
        help="Number of chunks to retrieve",
    )
    ask_parser.add_argument(
        "--mode",
        type=str,
        default="faiss",
        choices=["faiss", "hnsw", "bruteforce"],
        help="Retrieval mode",
    )

    args = parser.parse_args()

    if args.command == "build":
        rebuild_knowledge_base()

    elif args.command == "ask":
        if args.mode in {"faiss", "hnsw"} and not FAISS_AVAILABLE:
            raise RuntimeError(
                "FAISS is not installed.\n"
                "pip install faiss-cpu"
            )

        start = time.time()
        payload = answer_with_rag(
            args.question,
            top_k=args.top_k,
            mode=args.mode,
        )
        elapsed = time.time() - start

        print_results(payload)
        print(f"\nMode: {args.mode}")
        print(f"Elapsed: {elapsed:.2f}s")

if __name__ == "__main__":
    main()
