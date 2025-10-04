"""Utilities for obtaining and extracting keywords from job descriptions."""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List

import requests
from bs4 import BeautifulSoup

try:  # Optional heavy dependency is injected via requirements
    from trafilatura import extract as trafilatura_extract
except ImportError:  # pragma: no cover - fallback if package missing
    trafilatura_extract = None


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    # Some job boards behave better with an explicit referer
    "Referer": "https://www.google.com/",
}

# Basic English stopwords plus domain specific filler terms.
STOPWORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "doing",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "nor",
    "not",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "ought",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
    # job listing filler
    "responsibilities",
    "requirements",
    "preferred",
    "including",
    "experience",
    "skills",
    "team",
    "work",
    "years",
    "ability",
    "strong",
}


@dataclass
class KeywordExtractionResult:
    """Structured response holding intermediate keyword data."""

    keywords: List[str]
    source_text: str
    scraped_from_url: bool


def _extract_job_description_from_json(data) -> str:
    """Recursively search JSON structures for job description fields."""

    if isinstance(data, dict):
        type_value = data.get("@type") or data.get("type")
        if isinstance(type_value, str) and type_value.lower() in {"jobposting", "job"}:
            description = data.get("description") or data.get("responsibilities")
            if isinstance(description, str) and description.strip():
                return description

        # Heuristic fallback: some SPAs embed the description under generic keys
        # without the JobPosting schema. Accept sufficiently long text blocks.
        for key in (
            "description",
            "jobDescription",
            "job_description",
            "details",
            "summary",
            "body",
            "content",
        ):
            value = data.get(key)
            if isinstance(value, str) and len(value.strip()) > 120:
                return value

        for value in data.values():
            extracted = _extract_job_description_from_json(value)
            if extracted:
                return extracted
    elif isinstance(data, list):
        for item in data:
            extracted = _extract_job_description_from_json(item)
            if extracted:
                return extracted
    return ""


def _extract_json_ld_job_description(soup: BeautifulSoup) -> str:
    for script in soup.find_all("script"):
        type_attr = (script.get("type") or "").lower()
        if type_attr and "json" not in type_attr:
            continue

        raw_text = script.string or script.get_text() or ""
        raw_text = raw_text.strip()
        if not raw_text:
            continue

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            continue

        description_html = _extract_job_description_from_json(data)
        if not description_html:
            continue

        description = BeautifulSoup(description_html, "html.parser").get_text(" ")
        description = " ".join(description.split())
        if description:
            return description
    return ""


def _extract_meta_description(soup: BeautifulSoup) -> str:
    """Read description-like meta tags (og:description, description)."""
    # OpenGraph first
    og = soup.find("meta", attrs={"property": "og:description"})
    if og and og.get("content"):
        content = " ".join((og.get("content") or "").split())
        if len(content) > 80:
            return content

    # Standard description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        content = " ".join((meta_desc.get("content") or "").split())
        if len(content) > 80:
            return content
    return ""


def _extract_dom_job_description(soup: BeautifulSoup) -> str:
    """Heuristically extract the job description main content from common job boards.

    Uses a set of CSS selectors seen across LinkedIn, Indeed, Greenhouse, Lever, Workday,
    and many company career pages. Falls back to the largest plausible text block that
    contains job-specific keywords.
    """
    selectors = [
        '[data-test="job-description"]',
        '#jobDescriptionText',
        '.jobsearch-JobComponent-description',
        '.jobs-description__content',
        '.jobs-box__html-content',
        '.jobs-unified-description__content',
        '.jobs-description',
        '.job-description',
        '#jobDescription',
        '#description',
        'section[aria-label*="description" i]',
        'div[aria-label*="description" i]',
        'article[aria-label*="description" i]',
        'section[id*="description" i]',
        'div[id*="description" i]',
        'article[id*="description" i]',
        'section[class*="description" i]',
        'div[class*="description" i]',
        'article[class*="description" i]',
        # Common ATS / hostings
        '.posting-description',
        '.section-wrapper .description',
        '.content .job-description',
        '.content .description',
        '.jd-description',
        '.description__text',
        '.ats-description',
    ]

    def clean(txt: str) -> str:
        return " ".join((txt or "").split())

    best_text = ""
    best_score = 0

    # Try specific selectors first
    for sel in selectors:
        for node in soup.select(sel):
            text = node.get_text(" ")
            text = clean(text)
            # Basic gate to avoid nav or tiny snippets
            if len(text) < 200:
                continue
            # Score: prefer longer text with signals
            score = len(text)
            signals = [
                "responsibilit",
                "requirement",
                "qualification",
                "what you will",
                "what you'll",
                "about the role",
                "skills",
            ]
            lower_text = text.lower()
            score += sum(200 for s in signals if s in lower_text)
            if score > best_score:
                best_score = score
                best_text = text

    if best_text:
        return best_text

    # Fallback: choose the largest plausible block from semantic containers
    candidate_nodes = soup.find_all(["section", "article", "div"])
    for node in candidate_nodes:
        # Skip obvious non-content wrappers
        attributes = " ".join([
            node.get("id") or "",
            " ".join(node.get("class") or []),
            node.get("role") or "",
            node.get("aria-label") or "",
        ]).lower()
        if any(x in attributes for x in ["footer", "header", "nav", "sidebar", "cookie", "consent"]):
            continue

        text = clean(node.get_text(" "))
        if len(text) < 300:
            continue
        score = len(text)
        lower_text = text.lower()
        if any(k in lower_text for k in ["responsibilit", "requirement", "qualification", "experience", "skills"]):
            score += 400
        if score > best_score:
            best_score = score
            best_text = text

    return best_text


def _extract_trafilatura_text(html: str, url: str) -> str:
    if not trafilatura_extract:
        return ""
    try:
        extracted = trafilatura_extract(
            htmlstring=html,
            url=url,
            include_comments=False,
            include_tables=False,
            include_images=False,
        )
    except Exception:  # pragma: no cover - trafilatura may raise parsing errors
        return ""
    if not extracted:
        return ""
    return " ".join(extracted.split())


def fetch_job_description(url: str, *, timeout: int = 15) -> str:
    """Fetch raw text from a job description URL."""
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network errors
        raise RuntimeError(f"Unable to fetch job description: {exc}") from exc

    html_text = response.text
    soup = BeautifulSoup(html_text, "html.parser")

    fragments: List[str] = []

    json_ld_text = _extract_json_ld_job_description(soup)
    if json_ld_text:
        fragments.append(json_ld_text)

    dom_text = _extract_dom_job_description(soup)
    if dom_text:
        fragments.append(dom_text)

    meta_text = _extract_meta_description(soup)
    if meta_text:
        fragments.append(meta_text)

    ai_extracted_text = _extract_trafilatura_text(html_text, url)
    if ai_extracted_text:
        fragments.append(ai_extracted_text)

    # Remove non-content tags to focus on visible text.
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    text = " ".join(text.split())
    if text:
        fragments.append(text)

    combined = " ".join(fragments).strip()
    if not combined:
        raise RuntimeError("Parsed page does not contain text content.")
    return combined


def tokenize(text: str) -> Iterable[str]:
    """Tokenize text into keyword candidates while keeping tech tokens like c++."""
    lowered = text.lower()
    all_tokens = re.findall(r"[a-z0-9][a-z0-9\+\#\-\/]{1,}", lowered)
    for token in all_tokens:
        if token in STOPWORDS:
            continue
        if token.isnumeric():
            continue
        yield token


def _bigram_tokens(tokens: Iterable[str]) -> Counter:
    tokens_list = list(tokens)
    bigram_counter: Counter[str] = Counter()
    for i in range(len(tokens_list) - 1):
        first, second = tokens_list[i], tokens_list[i + 1]
        if first in STOPWORDS or second in STOPWORDS:
            continue
        bigram = f"{first} {second}"
        bigram_counter[bigram] += 1
    return bigram_counter


def extract_keywords(text: str, *, max_keywords: int = 30) -> List[str]:
    """Return a ranked list of relevant keywords pulled from free text."""
    token_stream = list(tokenize(text))
    if not token_stream:
        return []

    unigram_counts = Counter(token_stream)
    bigram_counts = _bigram_tokens(token_stream)

    scores: Counter[str] = Counter()
    for token, count in unigram_counts.items():
        # Slightly prefer longer technical tokens.
        scores[token] = count + (len(token) * 0.05)
    for token, count in bigram_counts.items():
        # Encourage multi-word phrases.
        scores[token] = max(scores[token], 0) + (count * 1.5) + (len(token) * 0.03)

    # Deduplicate while preserving order by score.
    sorted_tokens = sorted(
        scores.items(),
        key=lambda item: (-item[1], -len(item[0]), item[0]),
    )

    seen = set()
    keywords: List[str] = []
    for token, _score in sorted_tokens:
        # Skip single-letter leftovers.
        if len(token) < 2:
            continue
        if token in seen:
            continue
        # Avoid overlapping entries where the keyword is contained within a better phrase.
        if any(token in existing for existing in seen if " " in existing):
            continue
        seen.add(token)
        keywords.append(token)
        if len(keywords) >= max_keywords:
            break
    return keywords
