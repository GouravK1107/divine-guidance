import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INPUT_PATH = BASE_DIR / "data" / "bible" / "bible.json"

INDEX_PATH = BASE_DIR / "rag" / "bible.index"
METADATA_PATH = BASE_DIR / "rag" / "bible_metadata.json"


# ============================================================
# CONFIG
# ============================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Keep this low because your laptop was heating up
BATCH_SIZE = 8


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("BIBLE FAISS INDEX BUILDER")
print("=" * 60)

print(f"\nLoading JSON:")
print(INPUT_PATH)

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    records = json.load(f)

print(f"Loaded records: {len(records)}")


# ============================================================
# VALIDATE
# ============================================================

if not records:
    raise ValueError("Bible JSON is empty.")

for i, record in enumerate(records):
    if not record.get("text"):
        raise ValueError(f"Missing text at record {i}")

print("Validation passed.")


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading embedding model:")
print(MODEL_NAME)

model = SentenceTransformer(MODEL_NAME)

print("Model loaded.")


# ============================================================
# DETERMINE VECTOR DIMENSION
# ============================================================

dimension = model.get_sentence_embedding_dimension()

print(f"\nEmbedding dimension: {dimension}")


# ============================================================
# CREATE FAISS INDEX
# ============================================================

# Inner Product + normalized embeddings = cosine similarity
index = faiss.IndexFlatIP(dimension)

print("\nFAISS index created.")


# ============================================================
# BUILD INDEX IN BATCHES
# ============================================================

texts = [record["text"] for record in records]

total = len(texts)

print(f"\nBuilding embeddings...")
print(f"Total verses : {total}")
print(f"Batch size   : {BATCH_SIZE}")

for start in range(0, total, BATCH_SIZE):

    end = min(start + BATCH_SIZE, total)

    batch_texts = texts[start:end]

    embeddings = model.encode(
        batch_texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32
    )

    index.add(embeddings)

    processed = end

    percent = (processed / total) * 100

    print(
        f"Processed: {processed}/{total} "
        f"({percent:.1f}%)"
    )


# ============================================================
# VALIDATE INDEX
# ============================================================

print("\nValidating FAISS index...")

if index.ntotal != len(records):
    raise RuntimeError(
        f"Index count mismatch. "
        f"Index={index.ntotal}, Records={len(records)}"
    )

print(f"FAISS vectors: {index.ntotal}")


# ============================================================
# SAVE INDEX
# ============================================================

print("\nSaving FAISS index...")

faiss.write_index(
    index,
    str(INDEX_PATH)
)

print(f"Saved:")
print(INDEX_PATH)


# ============================================================
# SAVE METADATA
# ============================================================

print("\nSaving metadata...")

with open(METADATA_PATH, "w", encoding="utf-8") as f:
    json.dump(
        records,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"Saved:")
print(METADATA_PATH)


# ============================================================
# FINAL INFO
# ============================================================

print("\n" + "=" * 60)
print("BIBLE FAISS BUILD COMPLETE")
print("=" * 60)

print(f"Records          : {len(records)}")
print(f"Vectors          : {index.ntotal}")
print(f"Dimensions       : {dimension}")
print(f"Embedding model  : {MODEL_NAME}")
print(f"Index            : {INDEX_PATH}")
print(f"Metadata         : {METADATA_PATH}")

print("\nDone.")