"""Helpers for reconciling resume content and injecting hidden keyword blocks."""
from __future__ import annotations

import datetime as _dt
import re
from typing import Iterable, List, Tuple

MARKER_START = "% resume_helper keywords start"
MARKER_END = "% resume_helper keywords end"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def _collect_resume_terms(resume_content: str) -> Iterable[str]:
    tokens = re.findall(r"[a-z0-9][a-z0-9\+\#\-\/]{1,}", resume_content.lower())
    for token in tokens:
        if len(token) < 2:
            continue
        yield token


def find_missing_keywords(resume_content: str, candidate_keywords: List[str]) -> List[str]:
    """Return keywords absent from the resume content."""
    normalized_resume = _normalize(resume_content)
    resume_terms = set(_collect_resume_terms(resume_content))

    missing: List[str] = []
    for keyword in candidate_keywords:
        lowered = keyword.lower()
        if " " in lowered:
            if lowered in normalized_resume:
                continue
        else:
            if lowered in resume_terms:
                continue
        missing.append(keyword)
    return missing


def build_white_block(keywords: Iterable[str]) -> str:
    keyword_blob = " ".join(keywords)
    timestamp = _dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    block_lines = [
        MARKER_START,
        f"% generated {timestamp}",
        "\\par",
        f"{{\\color{{white}} {keyword_blob}}}",
        MARKER_END,
    ]
    return "\n".join(block_lines) + "\n"


def inject_white_keywords(
    resume_content: str,
    missing_keywords: List[str],
) -> Tuple[str, bool, List[str]]:
    """Inject keywords into resume content enclosed in white-colored block.

    Returns a tuple of (updated_resume_text, modified_flag, warnings).
    """
    warnings: List[str] = []
    cleaned_resume = remove_existing_block(resume_content)

    if not missing_keywords:
        return cleaned_resume, cleaned_resume != resume_content, warnings

    if "\\usepackage{xcolor}" not in resume_content and "\\usepackage{color}" not in resume_content:
        warnings.append(
            "Add \\usepackage{xcolor} to your preamble so the hidden keywords render correctly."
        )

    white_block = build_white_block(missing_keywords)
    
    # Insert white block BEFORE \end{document} so LaTeX actually processes it
    if "\\end{document}" in cleaned_resume:
        parts = cleaned_resume.rsplit("\\end{document}", 1)
        updated_resume = parts[0].rstrip() + "\n\n" + white_block + "\n\\end{document}" + parts[1]
    else:
        # Fallback: append at the end if no \end{document} found
        updated_resume = cleaned_resume.rstrip() + "\n\n" + white_block
        warnings.append(
            "Could not find \\end{document} in your LaTeX file. Keywords appended at the end."
        )
    
    return updated_resume, True, warnings


def remove_existing_block(resume_content: str) -> str:
    """Remove previously injected white keyword sections if present."""
    pattern = re.compile(
        rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}\n?",
        flags=re.DOTALL,
    )
    cleaned = re.sub(pattern, "", resume_content)
    return cleaned.rstrip() + "\n"
