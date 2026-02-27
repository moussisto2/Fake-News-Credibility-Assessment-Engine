from __future__ import annotations

# ---------------------------------------------------------------------
# RAISON "elements" (labels) and "options" (decisions)
# IMPORTANT: Python must send ONLY element IDs (OPT...) to RAISON.
# ---------------------------------------------------------------------

# Elements: label -> OPT id (from your GET metadata)
ELEMENTS = {
    "reputable_source": "OPT389218",
    "has_verifiable_source": "OPT389418",
    "clickbait_title": "OPT389468",
    "emotional_language_high": "OPT389518",
    "source_unverified": "OPT389568",
    "numbers_without_source": "OPT389618",
    "missing_context": "OPT389668",
    "neutral_tone": "OPT389718",
    "claims_without_evidence": "OPT389768",
    "extraordinary_claim": "OPT389818",
    "fact_check_failed": "OPT389868",
}

# Options: label -> OPT id (from your GET metadata)
OPTIONS = {
    "credible": "OPT389268",
    "needs_verification": "OPT389318",
    "likely_misinformation": "OPT389368",
}

# Deterministic local tie-break for multi-solution returns (multiple isSolution=true)
# Priority: misinformation > verification > credible
SOLUTION_PRIORITY = ["likely_misinformation", "needs_verification", "credible"]

# Inverse maps (convenient for display)
ELEMENT_ID_TO_LABEL = {v: k for k, v in ELEMENTS.items()}
OPTION_ID_TO_LABEL = {v: k for k, v in OPTIONS.items()}
