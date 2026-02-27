from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from fnce.core.schema import ELEMENTS
from fnce.utils.text import (
    all_caps_ratio,
    contains_any,
    exclamation_count,
    has_context_anchors,
    load_lexicons,
    normalize,
    numbers_count,
)
from fnce.utils.url import extract_domain, is_reputable_domain


@dataclass
class ExtractionResult:
    element_ids: set[str]
    evidence: dict[str, dict[str, Any]]  # label -> evidence details


Override = Literal["auto", "on", "off"]

_NEGATION_RE = re.compile(r"\b(no|not|without|unavailable|none|never|lacking)\b", re.IGNORECASE)
_DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
_URL_RE = re.compile(r"(https?://|www\.)\S+", re.IGNORECASE)


def _has_url(text: str) -> bool:
    return bool(_URL_RE.search(text or ""))


def _find_doi(text: str) -> str | None:
    m = _DOI_RE.search(text or "")
    return m.group(0) if m else None


def _negated_near(text: str, phrase: str, window: int = 28) -> bool:
    t = (text or "").lower()
    p = (phrase or "").lower().strip()
    if not p:
        return False
    idx = t.find(p)
    if idx < 0:
        return False
    start = max(0, idx - window)
    return bool(_NEGATION_RE.search(t[start:idx]))


def _detect_verifiable(full_text: str) -> tuple[bool, list[str]]:
    """
    STRICT verifiable evidence detection.

    Trigger has_verifiable_source ONLY when there are strong, concrete cues:
      - a URL inside the article text
      - a DOI
      - strong patterns implying traceable documents / datasets / protocol / code

    We intentionally ignore generic words like: study, report, experts, sources...
    """
    t = (full_text or "")
    tl = t.lower()
    hits: list[str] = []

    # 1) Concrete: URL present in TEXT
    if _has_url(t):
        hits.append("url_present")

    # 2) Concrete: DOI present
    doi = _find_doi(t)
    if doi:
        hits.append(f"doi:{doi}")

    # 3) Strong patterns (long list)
    strong_patterns = [
        "published in",
        "peer-reviewed",
        "peer reviewed",
        "systematic review",
        "meta-analysis",
        "randomized controlled trial",
        "double-blind",
        "placebo-controlled",
        "clinical trial",
        "trial registration",
        "registered trial",
        "registered at clinicaltrials.gov",
        "clinicaltrials.gov",
        "protocol available",
        "preprint available",
        "arxiv",
        "biorxiv",
        "medrxiv",
        "supplementary materials",
        "supplementary appendix",
        "appendix available",
        "methods section",
        "methodology described",
        "methodology is available",
        "replication code",
        "code available",
        "open-source code",
        "open source code",
        "github.com",
        "repository available",
        "data available",
        "dataset available",
        "downloadable dataset",
        "public dataset",
        "open dataset",
        "data portal",
        "data repository",
        "open data",
        "raw data",
        "data and code",
        "documentation available",
        "technical documentation",
        "white paper",
        "whitepaper",
        "government report",
        "official statistics",
        "press release",
        "official statement",
        "full report available",
        "read the full report",
        "pdf report",
        "source link",
        "source:",
        "references:",
        "citations:",
        "bibliography",
        "footnotes",
    ]

    for p in strong_patterns:
        if p in tl and not _negated_near(t, p):
            hits.append(f"pattern:{p}")
            break

    return (len(hits) > 0), hits[:12]


def extract_elements(
    title: str,
    content: str,
    source_url: str = "",
    *,
    overrides: dict[str, Override] | None = None,
) -> ExtractionResult:
    """
    Extract RAISON element IDs + evidence.

    overrides: tri-state for each label:
      - 'auto' (default)
      - 'on'   (force label ON)
      - 'off'  (force label OFF)

    Demo-friendly contradiction rules prevent opposite labels together.
    """
    overrides = dict(overrides or {})

    # normalize missing keys to auto
    for lbl in ELEMENTS.keys():
        overrides.setdefault(lbl, "auto")

    # ----------------------------
    # Contradiction rules
    # ----------------------------
    def force_off(label: str) -> None:
        if overrides.get(label) != "on":
            overrides[label] = "off"

    # reputable_source vs source_unverified
    if overrides["reputable_source"] == "on":
        force_off("source_unverified")
    if overrides["source_unverified"] == "on":
        force_off("reputable_source")

    # has_verifiable_source vs claims/numbers
    if overrides["has_verifiable_source"] == "on":
        force_off("claims_without_evidence")
        force_off("numbers_without_source")
    if overrides["claims_without_evidence"] == "on":
        force_off("has_verifiable_source")

    # neutral_tone vs sensational
    sensational = ["clickbait_title", "emotional_language_high", "extraordinary_claim"]
    if overrides["neutral_tone"] == "on":
        for s in sensational:
            force_off(s)
    if any(overrides[s] == "on" for s in sensational):
        force_off("neutral_tone")

    # ----------------------------
    # Start extraction
    # ----------------------------
    title_n = normalize(title)
    content_n = normalize(content)
    url_n = normalize(source_url)
    full_text = (title_n + "\n" + content_n).strip()
    lex = load_lexicons()

    fired: set[str] = set()
    ev: dict[str, dict[str, Any]] = {}

    def fire(label: str, reason: str, details: dict[str, Any] | None = None) -> None:
        fired.add(ELEMENTS[label])
        ev[label] = {"reason": reason, "details": details or {}}

    def is_forced_on(label: str) -> bool:
        return overrides.get(label) == "on"

    def is_forced_off(label: str) -> bool:
        return overrides.get(label) == "off"

    # ----------------------------
    # FACT CHECK FAILED (manual only)
    # ----------------------------
    if is_forced_on("fact_check_failed") and not is_forced_off("fact_check_failed"):
        fire("fact_check_failed", "manual: forced ON", {})

    # ----------------------------
    # SOURCE: reputable / unverified (based on URL allowlist)
    # ----------------------------
    domain = extract_domain(url_n)
    domain_is_rep = is_reputable_domain(domain) if domain else False

    if is_forced_on("reputable_source"):
        fire("reputable_source", "manual: forced ON", {"domain": domain})
    elif not is_forced_off("reputable_source"):
        if domain and domain_is_rep:
            fire("reputable_source", "auto: domain allowlist match", {"domain": domain})

    reputable_fired = ELEMENTS["reputable_source"] in fired

    if is_forced_on("source_unverified"):
        fire("source_unverified", "manual: forced ON", {"domain": domain})
    elif not is_forced_off("source_unverified"):
        if not reputable_fired:
            if not domain:
                fire("source_unverified", "auto: no source URL domain provided", {})
            else:
                fire("source_unverified", "auto: domain not in allowlist", {"domain": domain})

    # ----------------------------
    # VERIFIABLE SOURCE (strict)
    # ----------------------------
    auto_verifiable, evidence_hits = _detect_verifiable(full_text)

    if is_forced_on("has_verifiable_source"):
        fire("has_verifiable_source", "manual: forced ON", {"hits": evidence_hits})
        verifiable = True
    elif is_forced_off("has_verifiable_source"):
        verifiable = False
    else:
        verifiable = auto_verifiable
        if verifiable:
            fire("has_verifiable_source", "auto: strict evidence detected", {"hits": evidence_hits})

    # ----------------------------
    # CLICKBAIT TITLE
    # ----------------------------
    if is_forced_on("clickbait_title"):
        fire("clickbait_title", "manual: forced ON", {})
    elif not is_forced_off("clickbait_title"):
        cb_hits = contains_any(title_n, lex.get("clickbait_phrases", []))
        caps = all_caps_ratio(title_n)
        exc = exclamation_count(title_n)
        if cb_hits or caps >= 0.55 or exc >= 2:
            fire(
                "clickbait_title",
                "auto: clickbait phrases / ALL CAPS / exclamation marks",
                {"phrase_hits": cb_hits[:12], "all_caps_ratio": round(caps, 3), "exclamations": exc},
            )

    # ----------------------------
    # EMOTIONAL LANGUAGE HIGH
    # ----------------------------
    if is_forced_on("emotional_language_high"):
        fire("emotional_language_high", "manual: forced ON", {})
    elif not is_forced_off("emotional_language_high"):
        emo_hits = contains_any(full_text, lex.get("emotion_words", []))
        if len(emo_hits) >= 2 or exclamation_count(full_text) >= 4:
            fire(
                "emotional_language_high",
                "auto: emotion words / heavy punctuation",
                {"emotion_hits": emo_hits[:12], "exclamations": exclamation_count(full_text)},
            )

    # ----------------------------
    # EXTRAORDINARY CLAIM
    # ----------------------------
    if is_forced_on("extraordinary_claim"):
        fire("extraordinary_claim", "manual: forced ON", {})
    elif not is_forced_off("extraordinary_claim"):
        ex_hits = contains_any(full_text, lex.get("extraordinary_phrases", []))
        if ex_hits:
            fire("extraordinary_claim", "auto: extraordinary phrases", {"phrase_hits": ex_hits[:12]})

    # ----------------------------
    # CLAIMS WITHOUT EVIDENCE
    # ----------------------------
    if is_forced_on("claims_without_evidence"):
        fire("claims_without_evidence", "manual: forced ON", {})
    elif not is_forced_off("claims_without_evidence"):
        cert_hits = contains_any(full_text, lex.get("certainty_phrases", []))
        if cert_hits and not verifiable:
            fire(
                "claims_without_evidence",
                "auto: certainty language with no verifiable evidence",
                {"certainty_hits": cert_hits[:12], "evidence_hits": evidence_hits[:12]},
            )

    # ----------------------------
    # NUMBERS WITHOUT SOURCE (DEMO PATCH)
    # ----------------------------
    # For the demo, we do NOT penalize numeric claims if the source is reputable.
    # This avoids noisy false positives on credible domains.
    if is_forced_on("numbers_without_source"):
        fire("numbers_without_source", "manual: forced ON", {})
    elif not is_forced_off("numbers_without_source"):
        nums = numbers_count(full_text)
        if nums >= 3 and (not verifiable) and (not reputable_fired):
            fire(
                "numbers_without_source",
                "auto: many numbers but no verifiable evidence (and source not reputable)",
                {"numbers_count": nums},
            )

    # ----------------------------
    # MISSING CONTEXT
    # ----------------------------
    if is_forced_on("missing_context"):
        fire("missing_context", "manual: forced ON", {})
    elif not is_forced_off("missing_context"):
        context_hits = has_context_anchors(content_n)
        word_count = len((content_n or "").split())
        if word_count > 0 and word_count < 35 and len(context_hits) == 0:
            fire(
                "missing_context",
                "auto: short content with no context anchors",
                {"word_count": word_count, "context_hits": context_hits},
            )

    # ----------------------------
    # NEUTRAL TONE (weak)
    # ----------------------------
    if is_forced_on("neutral_tone"):
        fire("neutral_tone", "manual: forced ON", {})
    elif not is_forced_off("neutral_tone"):
        if (
            ELEMENTS["clickbait_title"] not in fired
            and ELEMENTS["emotional_language_high"] not in fired
            and ELEMENTS["extraordinary_claim"] not in fired
        ):
            fire("neutral_tone", "auto: no strong sensational/emotional/extraordinary markers", {})

    return ExtractionResult(element_ids=fired, evidence=ev)