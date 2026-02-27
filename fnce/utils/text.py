from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Iterable


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
URL_RE = re.compile(r"(https?://|www\.)\S+", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")


def _data_path(filename: str) -> Path:
    """
    Locate fnce/data/<filename>.
    """
    base = Path(__file__).resolve().parents[1]  # fnce/
    return base / "data" / filename


@lru_cache(maxsize=1)
def load_lexicons() -> dict[str, list[str]]:
    """
    Load lexicons from fnce/data/lexicons.json
    Returned keys:
      - clickbait_phrases
      - extraordinary_phrases
      - certainty_phrases
      - evidence_cues
      - emotion_words
    """
    path = _data_path("lexicons.json")
    if not path.exists():
        return {
            "clickbait_phrases": [],
            "extraordinary_phrases": [],
            "certainty_phrases": [],
            "evidence_cues": [],
            "emotion_words": [],
        }

    raw = json.loads(path.read_text(encoding="utf-8"))
    # Normalize to list[str]
    out: dict[str, list[str]] = {}
    for k in ["clickbait_phrases", "extraordinary_phrases", "certainty_phrases", "evidence_cues", "emotion_words"]:
        vals = raw.get(k, [])
        if not isinstance(vals, list):
            vals = []
        cleaned = []
        for v in vals:
            if isinstance(v, str):
                s = v.strip()
                if s:
                    cleaned.append(s)
        out[k] = cleaned
    return out


def normalize(text: str) -> str:
    return (text or "").strip()


def lower(text: str) -> str:
    return normalize(text).lower()


def contains_any(text: str, phrases: Iterable[str]) -> list[str]:
    """
    Return list of phrases that appear as substring (case-insensitive).
    """
    t = lower(text)
    hits = []
    for p in phrases:
        if not isinstance(p, str):
            continue
        if p.lower() in t:
            hits.append(p)
    return hits


def exclamation_count(text: str) -> int:
    return normalize(text).count("!")


def all_caps_ratio(text: str) -> float:
    """
    Ratio of uppercase letters among all alphabetic letters.
    """
    t = normalize(text)
    letters = [c for c in t if c.isalpha()]
    if not letters:
        return 0.0
    upper = sum(1 for c in letters if c.isupper())
    return upper / len(letters)


def contains_url(text: str) -> bool:
    return bool(URL_RE.search(text or ""))


def find_doi(text: str) -> str | None:
    m = DOI_RE.search(text or "")
    return m.group(0) if m else None


def has_evidence_cues(text: str) -> list[str]:
    """
    Evidence cue hits, including URL and DOI detection.
    """
    lex = load_lexicons()
    cues = lex.get("evidence_cues", [])
    hits = contains_any(text, cues)

    if contains_url(text):
        hits.append("url_present")

    doi = find_doi(text)
    if doi:
        hits.append(f"doi:{doi}")

    return hits


def numbers_count(text: str) -> int:
    """
    Count numeric tokens like 10, 10%, 1.2, 1,000
    """
    t = normalize(text)
    return len(re.findall(r"\b\d[\d,\.]*%?\b", t))


def has_context_anchors(text: str) -> list[str]:
    """
    Lightweight context anchor detection (who/when/where).
    Used to avoid false positives for missing_context.
    """
    t = normalize(text)
    hits: list[str] = []

    if YEAR_RE.search(t):
        hits.append("year_present")

    # Simple temporal/spatial words
    if any(w in lower(t) for w in ["today", "yesterday", "this week", "in ", "at ", "on "]):
        hits.append("time_or_location_words")

    # Rough proxy for named entities: multiple capitalized tokens
    cap_tokens = re.findall(r"\b[A-Z][a-z]{2,}\b", t)
    if len(cap_tokens) >= 2:
        hits.append("capitalized_entities")

    # Quotes with attribution proxy
    if '"' in t and any(w in lower(t) for w in ["said", "according to", "stated"]):
        hits.append("quote_attribution")

    return hits
