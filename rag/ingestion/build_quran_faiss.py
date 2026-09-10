import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "quran"
    / "quran.json"
)

RAG_DIR = (
    BASE_DIR
    / "rag"
)

INDEX_PATH = (
    RAG_DIR
    / "quran.index"
)

METADATA_PATH = (
    RAG_DIR
    / "quran_metadata.json"
)


# Same model used for Gita
MODEL_NAME = (
    "sentence-transformers/all-mpnet-base-v2"
)


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 60)
print("QURAN FAISS INDEX BUILDER")
print("=" * 60)

print("\nLoading embedding model...")
print(f"Model: {MODEL_NAME}")

model = SentenceTransformer(
    MODEL_NAME
)

print("✓ Embedding model loaded")


# ============================================================
# LOAD DATASET
# ============================================================

print("\nLoading Quran dataset...")

with open(
    DATA_PATH,
    "r",
    encoding="utf-8"
) as file:

    data = json.load(file)


print(
    f"✓ Loaded {len(data)} records"
)


# ============================================================
# PREPARE RETRIEVAL TEXT
# ============================================================

texts = []

for item in data:

    text = (
        item.get("text", "")
        .strip()
    )

    if not text:
        text = "No Quran translation available."

    texts.append(text)


print(
    f"✓ Prepared {len(texts)} retrieval texts"
)


# ============================================================
# CREATE EMBEDDINGS
# ============================================================

print("\nCreating embeddings...")

embeddings = model.encode(
    texts,
    convert_to_numpy=True,
    normalize_embeddings=True,
    show_progress_bar=True
)

embeddings = embeddings.astype(
    np.float32
)

print(
    f"✓ Embeddings shape: "
    f"{embeddings.shape}"
)


# ============================================================
# CREATE FAISS INDEX
# ============================================================

dimension = embeddings.shape[1]

print(
    f"\nEmbedding dimension: {dimension}"
)

# Normalized vectors + inner product
# = cosine similarity

index = faiss.IndexFlatIP(
    dimension
)

index.add(
    embeddings
)

print(
    f"✓ FAISS index contains "
    f"{index.ntotal} vectors"
)


# ============================================================
# SAVE INDEX
# ============================================================

RAG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

faiss.write_index(
    index,
    str(INDEX_PATH)
)

print(
    f"✓ Index saved: {INDEX_PATH}"
)


# ============================================================
# SAVE METADATA
# ============================================================

metadata = []

for item in data:

    metadata.append({

        "tradition": item.get(
            "tradition",
            "quran"
        ),

        "book": item.get(
            "book",
            "Quran"
        ),

        "chapter": item.get(
            "chapter"
        ),

        "chapter_name": item.get(
            "chapter_name"
        ),

        "verse": item.get(
            "verse"
        ),

        "text": item.get(
            "text",
            ""
        ),

        "source": item.get(
            "source",
            ""
        ),

        "translation": item.get(
            "translation",
            ""
        ),

        "translation_attribution": item.get(
            "translation_attribution",
            ""
        ),

        "translation_license": item.get(
            "translation_license",
            ""
        ),
    })


with open(
    METADATA_PATH,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        metadata,
        file,
        ensure_ascii=False,
        indent=2
    )


print(
    f"✓ Metadata saved: "
    f"{METADATA_PATH}"
)


# ============================================================
# TEST RETRIEVAL
# ============================================================

print("\n" + "=" * 60)
print("TEST RETRIEVAL")
print("=" * 60)


TEST_QUERIES = [

    "I am confused about what I should do in life",

    "I feel completely directionless and don't know "
    "which path I should take",

    "I am struggling to control my desires",

    "I get angry very easily",

    "I am going through a difficult time "
    "and need patience",

    "I have lost my motivation and don't feel like "
    "doing anything",

]


for test_query in TEST_QUERIES:

    print("\n" + "-" * 60)

    print(
        f"Query: {test_query}"
    )

    print("-" * 60)

    query_embedding = model.encode(
        [test_query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    query_embedding = query_embedding.astype(
        np.float32
    )

    scores, indices = index.search(
        query_embedding,
        10
    )

    for rank, (
        score,
        idx
    ) in enumerate(
        zip(
            scores[0],
            indices[0]
        ),
        start=1
    ):

        if idx < 0:
            continue

        item = metadata[idx]

        print(
            f"{rank:>2}. "
            f"{item['source']} "
            f"(score={score:.4f})"
        )

        print(
            f"    {item['text'][:180]}"
        )


# ============================================================
# DONE
# ============================================================

print("\n" + "=" * 60)
print("QURAN FAISS BUILD COMPLETE")
print("=" * 60)