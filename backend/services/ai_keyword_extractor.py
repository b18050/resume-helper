"""Optional OpenAI-powered keyword extraction helpers."""
from __future__ import annotations

import json
import logging
import os
import re
from typing import List

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency
    OpenAI = None  # type: ignore

LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4.1-mini"
SYSTEM_PROMPT = (
    "You analyse job descriptions and list the most relevant skills, tools, "
    "and domain keywords. Return a short JSON object with a `keywords` array."
)


def _is_enabled() -> bool:
    return bool(OpenAI) and bool(os.getenv("OPENAI_API_KEY"))


def _build_payload(job_text: str, resume_text: str, max_keywords: int) -> List[dict]:
    instructions = (
        "Extract the top focus keywords the resume should contain."
        f" Include up to {max_keywords} distinct items."
        " Skip duplicates, generic stop words, and company names unless vital."
    )

    parts = [
        {
            "type": "text",
            "text": instructions,
        },
        {
            "type": "text",
            "text": "Job description:\n" + job_text.strip(),
        },
    ]

    if resume_text.strip():
        parts.append(
            {
                "type": "text",
                "text": "Existing resume content (for reference, do not paraphrase):\n" + resume_text,
            }
        )

    return [
        {
            "role": "system",
            "content": [{"type": "text", "text": SYSTEM_PROMPT}],
        },
        {
            "role": "user",
            "content": parts,
        },
    ]


def extract_keywords_via_openai(
    job_text: str,
    resume_text: str = "",
    *,
    max_keywords: int = 30,
) -> List[str]:
    """Use the OpenAI Responses API to pull structured keywords.

    Returns an empty list when the integration is not configured or on errors.
    """
    if not job_text.strip():
        return []
    if not _is_enabled():
        return []

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

    try:
        client = OpenAI(api_key=api_key)
    except Exception as exc:  # pragma: no cover - environment misconfig
        LOGGER.warning("Failed to initialise OpenAI client", exc_info=exc)
        return []

    try:
        response = client.responses.create(
            model=model,
            input=_build_payload(job_text, resume_text, max_keywords),
            temperature=0.15,
            max_output_tokens=600,
        )
        raw_output = response.output_text.strip()
    except Exception as exc:  # pragma: no cover - API error
        LOGGER.warning("OpenAI keyword extraction request failed", exc_info=exc)
        return []

    if not raw_output:
        return []

    keywords: List[str] = []
    try:
        payload = json.loads(raw_output)
        maybe_keywords = payload.get("keywords")
        if isinstance(maybe_keywords, list):
            for item in maybe_keywords:
                if isinstance(item, str):
                    cleaned = item.strip()
                    if cleaned:
                        keywords.append(cleaned)
    except json.JSONDecodeError:
        # Fallback: split by newlines or commas
        for chunk in re.split(r"[\n,]", raw_output):
            candidate = chunk.strip(" \t-•")
            if len(candidate) > 1:
                keywords.append(candidate)
    except Exception as exc:  # pragma: no cover
        LOGGER.debug("Unexpected error parsing OpenAI output", exc_info=exc)

    # Deduplicate preserving order.
    seen = set()
    ordered: List[str] = []
    for keyword in keywords:
        lowered = keyword.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(keyword)
        if len(ordered) >= max_keywords:
            break
    return ordered
