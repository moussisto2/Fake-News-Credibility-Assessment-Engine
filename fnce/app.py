from __future__ import annotations

import streamlit as st

from fnce.config import load_settings
from fnce.core.decision import assess_credibility


st.set_page_config(page_title="Fake News Credibility Assessment Engine", layout="wide")


LABELS_ORDER = [
    "reputable_source",
    "source_unverified",
    "has_verifiable_source",
    "claims_without_evidence",
    "numbers_without_source",
    "missing_context",
    "neutral_tone",
    "clickbait_title",
    "emotional_language_high",
    "extraordinary_claim",
    "fact_check_failed",
]


def tri_state(label: str) -> str:
    # returns one of: "auto" / "on" / "off"
    choice = st.selectbox(
        label,
        options=["Auto", "Force ON", "Force OFF"],
        index=0,
        key=f"override_{label}",
    )
    return {"Auto": "auto", "Force ON": "on", "Force OFF": "off"}[choice]


def main() -> None:
    settings = load_settings()

    st.title("Fake News Credibility Assessment Engine")
    st.caption("Lightweight NLP signals → RAISON elements (OPT...) → Explainable decision options")

    with st.sidebar:
        st.header("Manual label controls")
        st.caption("Each label can be Auto / Force ON / Force OFF. Contradictions are handled automatically by the extractor.")

        overrides = {}
        for lbl in LABELS_ORDER:
            overrides[lbl] = tri_state(lbl)

        st.divider()
        st.caption("Tip: for a strong 'credible' demo, force ON reputable_source + has_verifiable_source, and keep negatives Auto/OFF.")

    col1, col2 = st.columns([1, 1], gap="large")
    with col1:
        title = st.text_input("Headline / Title", value="", placeholder="Enter the headline...")
        url = st.text_input("Source URL (optional)", value="", placeholder="https://...")
    with col2:
        text = st.text_area(
            "Article text (optional but recommended)",
            value="",
            height=220,
            placeholder="Paste article text here...",
        )

    if st.button("Analyze", type="primary"):
        if not title.strip() and not text.strip():
            st.error("Please provide at least a title or some text.")
            return

        try:
            result = assess_credibility(
                title=title,
                content=text,
                source_url=url,
                settings=settings,
                overrides=overrides,
            )
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            return

        st.subheader("Extracted RAISON elements (labels → IDs)")
        st.dataframe(result["elements_table"], use_container_width=True)

        with st.expander("Evidence (why each label fired)"):
            st.json(result["evidence"], expanded=False)

        st.subheader("RAISON decision")
        st.write(f"**Verdict:** `{result['decision_label']}`")
        st.write(f"**Option ID:** `{result['decision_id']}`")

        st.subheader("RAISON explanations (merged)")
        if result["explanations"]:
            for line in result["explanations"]:
                st.write("- " + line)
        else:
            st.info("No explanation lines returned.")

        with st.expander("Raw RAISON response"):
            st.json(result["raw_raison"], expanded=False)


if __name__ == "__main__":
    main()