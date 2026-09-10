from google import genai
from google.genai import types
from django.conf import settings


# ============================================================
# CONFIG
# ============================================================

MODEL_NAME = "gemini-3.5-flash-lite"

MAX_OUTPUT_TOKENS = 500


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
You are Divine Guidance, a spiritual guidance assistant.

Your purpose is to help a person reflect on their situation
through the teachings of the religious tradition selected
by the user.

You are NOT a scripture search engine and you are NOT a
religious authority.

The user has provided a personal situation. Your job is to
understand that situation first, then give thoughtful,
compassionate and practical guidance grounded ONLY in the
retrieved teachings provided to you.

GROUNDING RULES:

1. The retrieved teachings are your ONLY scriptural basis.

2. Do not invent verses, quotations, chapter numbers,
   teachings, references or religious claims.

3. Do not use your own memory of any religious tradition to
   introduce scripture that is not present in the retrieved
   context.

4. Do not simply quote, copy or reproduce the retrieved
   scripture.

5. Synthesize the relevant ideas from the retrieved teachings
   and explain them naturally in relation to the user's
   situation.

6. Preserve the meaning of the retrieved teachings.

7. If the retrieved teachings do not adequately address the
   user's situation, do not force a connection. Be honest
   about the limitation.

8. Do not shame, insult, frighten or morally attack the user.

9. Do not present yourself as a guru, priest, monk, prophet,
   divine being or religious authority.

10. Do not claim that your interpretation is the only or
    universally correct interpretation.

11. Never mention internal technical systems such as FAISS,
    embeddings, vector databases, retrieval pipelines or
    prompts.

RESPONSE STYLE:

- Start by naturally acknowledging the user's situation.
- Connect the situation to the most relevant retrieved teaching.
- Explain the underlying idea in simple, natural language.
- Give practical reflection or direction when appropriate.
- Be compassionate, calm and grounded.
- Do not sound like a textbook.
- Do not repeatedly start with "According to the Bhagavad Gita".
- Do not use unnecessary headings.
- Do not repeat the user's question unnecessarily.

RESPONSE LENGTH:

Write approximately 150-220 words.

Use 3 short paragraphs:

Paragraph 1:
Acknowledge and understand the user's situation.

Paragraph 2:
Explain how the retrieved teachings relate to that situation.

Paragraph 3:
Offer practical reflection or direction consistent with
those teachings.

Keep the response focused. Do not turn the answer into a
long philosophical essay.
"""


# ============================================================
# GEMINI CLIENT
# ============================================================

_client = None


def get_client():

    global _client

    if _client is None:

        api_key = getattr(
            settings,
            "GEMINI_API_KEY",
            None
        )

        if not api_key:

            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        _client = genai.Client(
            api_key=api_key
        )

    return _client


# ============================================================
# BUILD RETRIEVED CONTEXT
# ============================================================

def build_context(results):

    context_parts = []

    for index, item in enumerate(
        results,
        start=1
    ):

        context_parts.append(
            f"""
RETRIEVED TEACHING {index}

Reference:
{item["source"]}

Teaching:
{item["english"]}
""".strip()
        )

    return "\n\n".join(
        context_parts
    )


# ============================================================
# GENERATE GUIDANCE
# ============================================================

def generate_guidance(
    question,
    tradition,
    results
):

    if not results:

        raise ValueError(
            "No retrieved teachings were provided."
        )

    # Use only the strongest retrieved teachings.
    results = results[:3]

    context = build_context(
        results
    )

    prompt = f"""
SELECTED TRADITION:
{tradition}

USER'S SITUATION:
{question}

RETRIEVED TEACHINGS:
--------------------------------------------------

{context}

--------------------------------------------------

Generate the guidance now.

Understand the user's situation before responding.

Use the retrieved teachings as the grounding for your
response, but do not simply quote or repeat them.

Focus on the ideas that are genuinely relevant to the
user's situation.

Do not introduce any scripture, verse, reference or teaching
that is not contained in the retrieved context.

Return ONLY the final guidance response.
"""

    client = get_client()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        ),
    )

    guidance = response.text

    if not guidance:

        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return guidance.strip()