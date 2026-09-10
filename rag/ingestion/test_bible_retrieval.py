import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INDEX_PATH = BASE_DIR / "rag" / "bible.index"
METADATA_PATH = BASE_DIR / "rag" / "bible_metadata.json"


# ============================================================
# CONFIG
# ============================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 5


# ============================================================
# TEST QUERIES
# ============================================================

QUERIES = [
    "I am confused about what I should do in life",

    "I feel completely directionless and don't know what to do",

    "I am struggling to control my desires",

    "I get angry very easily",

    "I am going through a difficult time and need patience",

    "I have lost my motivation and feel empty",
]


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 70)
print("BIBLE RETRIEVAL TEST")
print("=" * 70)

print("\nLoading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("Model loaded.")


# ============================================================
# LOAD FAISS INDEX
# ============================================================

print("\nLoading FAISS index...")

index = faiss.read_index(str(INDEX_PATH))

print(f"FAISS vectors: {index.ntotal}")


# ============================================================
# LOAD METADATA
# ============================================================

print("\nLoading metadata...")

with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)

print(f"Metadata records: {len(metadata)}")


# ============================================================
# VALIDATION
# ============================================================

if index.ntotal != len(metadata):
    raise RuntimeError(
        f"Mismatch! "
        f"Index={index.ntotal}, Metadata={len(metadata)}"
    )

print("Index and metadata count match.")


# ============================================================
# RETRIEVAL FUNCTION
# ============================================================

def retrieve(query, top_k=TOP_K):

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype=np.float32
    )

    scores, indices = index.search(
        query_embedding,
        top_k
    )

    results = []

    for score, idx in zip(scores[0], indices[0]):

        if idx == -1:
            continue

        record = metadata[idx]

        results.append({
            "score": float(score),
            "source": record.get("source", ""),
            "book": record.get("book", ""),
            "chapter": record.get("chapter"),
            "verse": record.get("verse"),
            "text": record.get("text", ""),
        })

    return results


# ============================================================
# RUN TESTS
# ============================================================

for number, query in enumerate(QUERIES, start=1):

    print("\n")
    print("=" * 70)
    print(f"TEST {number}")
    print("=" * 70)

    print(f"\nQUERY:")
    print(query)

    results = retrieve(query)

    print("\nTOP RESULTS:")

    for rank, result in enumerate(results, start=1):

        print("\n" + "-" * 70)

        print(
            f"#{rank} | "
            f"{result['source']} | "
            f"Score: {result['score']:.4f}"
        )

        print(result["text"])


# ============================================================
# DONE
# ============================================================

print("\n")
print("=" * 70)
print("BIBLE RETRIEVAL TEST COMPLETE")
print("=" * 70)