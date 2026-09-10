from pathlib import Path
import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from rag.generation.guidance_generator import generate_guidance


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAG_DIR = BASE_DIR / "rag"


# ============================================================
# RAG CONFIG
# ============================================================

TOP_K = 5


# ============================================================
# TRADITION CONFIG
#
# Each tradition has:
#   - its own FAISS index
#   - its own metadata
#   - its own embedding model
#
# Gita + Quran use MPNet.
# Bible uses lightweight MiniLM.
# ============================================================

TRADITION_CONFIG = {

    "gita": {
        "index": RAG_DIR / "gita.index",
        "metadata": RAG_DIR / "gita_metadata.json",
        "label": "Bhagavad Gita",
        "model": "sentence-transformers/all-mpnet-base-v2",
    },

    "quran": {
        "index": RAG_DIR / "quran.index",
        "metadata": RAG_DIR / "quran_metadata.json",
        "label": "Quran",
        "model": "sentence-transformers/all-mpnet-base-v2",
    },

    "bible": {
        "index": RAG_DIR / "bible.index",
        "metadata": RAG_DIR / "bible_metadata.json",
        "label": "Bible",
        "model": "sentence-transformers/all-MiniLM-L6-v2",
    },

}


# ============================================================
# LOAD EMBEDDING MODELS ONCE
# ============================================================

# Cache models by model name.
#
# This means:
#
# Gita  ─┐
#        ├── MPNet (one shared instance)
# Quran ─┘
#
# Bible ─── MiniLM
#
_embedding_models = {}


def get_embedding_model(tradition):
    """
    Load the correct embedding model for the selected
    religious tradition and reuse it on future requests.
    """

    if tradition not in TRADITION_CONFIG:
        raise ValueError(
            f"Unsupported tradition: {tradition}"
        )

    model_name = TRADITION_CONFIG[tradition]["model"]

    # Return cached model if already loaded.
    if model_name in _embedding_models:
        return _embedding_models[model_name]

    print(
        f"Loading embedding model for {tradition}: "
        f"{model_name}"
    )

    model = SentenceTransformer(model_name)

    _embedding_models[model_name] = model

    print(
        f"Embedding model loaded: {model_name}"
    )

    return model


# ============================================================
# LOAD RAG COMPONENTS ONCE
# ============================================================

_rag_cache = {}


def load_rag_components(tradition):
    """
    Load the FAISS index and metadata for the
    selected tradition.

    Each tradition is cached separately.
    """

    if tradition not in TRADITION_CONFIG:
        raise ValueError(
            f"Unsupported tradition: {tradition}"
        )

    # --------------------------------------------------------
    # Return cached components if already loaded.
    # --------------------------------------------------------

    if tradition in _rag_cache:
        return _rag_cache[tradition]

    config = TRADITION_CONFIG[tradition]

    index_path = config["index"]
    metadata_path = config["metadata"]

    # --------------------------------------------------------
    # Check index
    # --------------------------------------------------------

    if not index_path.exists():

        raise FileNotFoundError(
            f"FAISS index not found: {index_path}"
        )

    # --------------------------------------------------------
    # Check metadata
    # --------------------------------------------------------

    if not metadata_path.exists():

        raise FileNotFoundError(
            f"Metadata file not found: {metadata_path}"
        )

    # --------------------------------------------------------
    # Load index
    # --------------------------------------------------------

    index = faiss.read_index(
        str(index_path)
    )

    # --------------------------------------------------------
    # Load metadata
    # --------------------------------------------------------

    with open(
        metadata_path,
        "r",
        encoding="utf-8"
    ) as file:

        metadata = json.load(file)

    # --------------------------------------------------------
    # Validate index / metadata count
    # --------------------------------------------------------

    if index.ntotal != len(metadata):

        raise ValueError(
            f"RAG data mismatch for {tradition}: "
            f"index has {index.ntotal} vectors, "
            f"metadata has {len(metadata)} records."
        )

    # --------------------------------------------------------
    # Cache
    # --------------------------------------------------------

    _rag_cache[tradition] = (
        index,
        metadata
    )

    return (
        index,
        metadata
    )


# ============================================================
# NORMALIZE METADATA
# ============================================================

def normalize_result(item, score):
    """
    Convert tradition-specific metadata into one common
    structure expected by the frontend and Gemini.

    Gita uses:
        english

    Quran uses:
        text

    Bible uses:
        text

    Internally we expose all of them as:
        english
    """

    english_text = (
        item.get("english")
        or item.get("text")
        or ""
    )

    return {
        "chapter": item.get(
            "chapter"
        ),

        "verse": item.get(
            "verse"
        ),

        "sanskrit": item.get(
            "sanskrit",
            ""
        ),

        "english": english_text,

        "source": item.get(
            "source",
            ""
        ),

        "score": round(
            float(score),
            4
        ),
    }


# ============================================================
# HOME
# ============================================================

def home(request):

    return render(
        request,
        "index.html"
    )


# ============================================================
# GUIDANCE API
# ============================================================

@require_POST
def guidance_api(request):

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        body = json.loads(
            request.body
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                "error": (
                    "Invalid JSON request."
                )
            },
            status=400
        )

    # --------------------------------------------------------
    # Get input
    # --------------------------------------------------------

    tradition = (
        body.get("source")
        or body.get("tradition")
    )

    question = body.get(
        "question",
        ""
    )

    # --------------------------------------------------------
    # Validate tradition
    # --------------------------------------------------------

    if not tradition:

        return JsonResponse(
            {
                "error": (
                    "Please select a source."
                )
            },
            status=400
        )

    tradition = (
        tradition
        .strip()
        .lower()
    )

    # --------------------------------------------------------
    # Check supported tradition
    # --------------------------------------------------------

    if tradition not in TRADITION_CONFIG:

        return JsonResponse(
            {
                "error": (
                    "This source is not available yet."
                )
            },
            status=400
        )

    label = TRADITION_CONFIG[
        tradition
    ]["label"]

    # --------------------------------------------------------
    # Validate question
    # --------------------------------------------------------

    if not isinstance(
        question,
        str
    ):

        return JsonResponse(
            {
                "error": (
                    "Question must be text."
                )
            },
            status=400
        )

    question = question.strip()

    if not question:

        return JsonResponse(
            {
                "error": (
                    "Please tell us what is on your mind."
                )
            },
            status=400
        )

    # Keep requests reasonable.
    if len(question) > 2000:

        return JsonResponse(
            {
                "error": (
                    "Please keep your question "
                    "under 2000 characters."
                )
            },
            status=400
        )

    # ========================================================
    # LOAD EMBEDDING MODEL + RAG
    # ========================================================

    try:

        # IMPORTANT:
        # The model is selected according to tradition.
        #
        # Gita  -> MPNet
        # Quran -> MPNet
        # Bible -> MiniLM

        model = get_embedding_model(
            tradition
        )

        index, metadata = (
            load_rag_components(
                tradition
            )
        )

    except Exception as exc:

        print(
            "RAG loading error:",
            exc
        )

        return JsonResponse(
            {
                "error": (
                    "The guidance system could not "
                    "load its retrieval components."
                )
            },
            status=500
        )

    # ========================================================
    # CREATE QUERY EMBEDDING
    # ========================================================

    try:

        query_embedding = model.encode(
            [question],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        query_embedding = (
            query_embedding.astype(
                np.float32
            )
        )

    except Exception as exc:

        print(
            "Embedding error:",
            exc
        )

        return JsonResponse(
            {
                "error": (
                    "Could not process the question."
                )
            },
            status=500
        )

    # ========================================================
    # FAISS SEARCH
    # ========================================================

    try:

        scores, indices = index.search(
            query_embedding,
            TOP_K
        )

    except Exception as exc:

        print(
            "FAISS search error:",
            exc
        )

        return JsonResponse(
            {
                "error": (
                    "Could not search the guidance library."
                )
            },
            status=500
        )

    # ========================================================
    # BUILD RESULTS
    # ========================================================

    results = []

    for score, index_position in zip(
        scores[0],
        indices[0]
    ):

        if index_position < 0:
            continue

        if index_position >= len(
            metadata
        ):
            continue

        item = metadata[
            int(index_position)
        ]

        result = normalize_result(
            item,
            score
        )

        results.append(
            result
        )

    # ========================================================
    # NO RESULTS
    # ========================================================

    if not results:

        return JsonResponse(
            {
                "error": (
                    "No relevant teaching was found."
                )
            },
            status=404
        )

    # ========================================================
    # GEMINI GUIDANCE GENERATION
    # ========================================================

    try:

        guidance = generate_guidance(
            question=question,
            tradition=label,
            results=results[:3],
        )

    except Exception as exc:

        print(
            "Guidance generation error:",
            exc
        )

        return JsonResponse(
            {
                "error": (
                    "The guidance could not be generated "
                    "right now."
                )
            },
            status=500
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return JsonResponse(
        {
            "success": True,

            "tradition": tradition,

            "label": label,

            "question": question,

            "guidance": guidance,

            "result": results[0],

            "results": results,
        }
    )