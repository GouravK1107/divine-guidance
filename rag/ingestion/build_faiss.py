""" import json
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
    / "gita"
    / "gita.json"
)

RAG_DIR = (
    BASE_DIR
    / "rag"
)

INDEX_PATH = (
    RAG_DIR
    / "gita.index"
)

METADATA_PATH = (
    RAG_DIR
    / "gita_metadata.json"
)


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 60)
print("GITA FAISS INDEX BUILDER")
print("=" * 60)

print("\nLoading embedding model...")

model = SentenceTransformer(
    MODEL_NAME
)

print("✓ Embedding model loaded")


# ============================================================
# LOAD JSON
# ============================================================

print("\nLoading Gita dataset...")

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
# PREPARE TEXT FOR EMBEDDING
# ============================================================

texts = []

for item in data:

    # English is used for semantic retrieval.
    #
    # Sanskrit is preserved in metadata and returned
    # to the frontend.
    #
    # We can later experiment with:
    #
    # English + Sanskrit
    #
    # embeddings as well.

    text = (
        item["english"]
        .strip()
    )

    texts.append(text)


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

# Inner Product + normalized vectors
# = cosine similarity

index = faiss.IndexFlatIP(
    dimension
)

index.add(
    embeddings.astype(
        np.float32
    )
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
        "tradition": item["tradition"],
        "book": item["book"],
        "chapter": item["chapter"],
        "verse": item["verse"],
        "sanskrit": item["sanskrit"],
        "english": item["english"],
        "source": item["source"],
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
# TEST SEARCH
# ============================================================

print("\n" + "=" * 60)
print("TEST RETRIEVAL")
print("=" * 60)

test_query = (
    "I am confused about what I should do in life"
)

query_embedding = model.encode(
    [test_query],
    convert_to_numpy=True,
    normalize_embeddings=True
)

scores, indices = index.search(
    query_embedding.astype(
        np.float32
    ),
    5
)


print(
    f"\nQuery: {test_query}\n"
)

for rank, (
    score,
    idx
) in enumerate(
    zip(scores[0], indices[0]),
    start=1
):

    if idx == -1:
        continue

    item = metadata[idx]

    print(
        f"{rank}. "
        f"{item['source']} "
        f"(score={score:.4f})"
    )

    print(
        f"   {item['english'][:200]}"
    )

    print()


# ============================================================
# DONE
# ============================================================

print("=" * 60)
print("FAISS BUILD COMPLETE")
print("=" * 60) """

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
    / "gita"
    / "gita.json"
)

RAG_DIR = (
    BASE_DIR
    / "rag"
)

INDEX_PATH = (
    RAG_DIR
    / "gita.index"
)

METADATA_PATH = (
    RAG_DIR
    / "gita_metadata.json"
)


# Stronger semantic embedding model
MODEL_NAME = (
    "sentence-transformers/all-mpnet-base-v2"
)


# ============================================================
# LOAD MODEL
# ============================================================

print("=" * 60)
print("GITA FAISS INDEX BUILDER")
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

print("\nLoading Gita dataset...")

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

    english = (
        item.get("english", "")
        .strip()
    )

    if not english:
        english = (
            "No English translation available."
        )

    texts.append(english)


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
        "tradition": item["tradition"],
        "book": item["book"],
        "chapter": item["chapter"],
        "verse": item["verse"],
        "sanskrit": item["sanskrit"],
        "english": item["english"],
        "source": item["source"],
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

    "I am afraid of failing",

    "I am struggling to control my desires",

    "I get angry very easily",

    "I have lost my motivation and don't feel like doing anything",

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
            f"    {item['english'][:180]}"
        )


# ============================================================
# DONE
# ============================================================

print("\n" + "=" * 60)
print("FAISS BUILD COMPLETE")
print("=" * 60)