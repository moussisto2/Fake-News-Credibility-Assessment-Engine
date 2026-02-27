from __future__ import annotations

import pandas as pd

from fnce.config import Settings
from fnce.core.extractor import extract_elements, Override
from fnce.core.raison_client import RaisonClient
from fnce.core.schema import ELEMENTS


def assess_credibility(
    *,
    title: str,
    content: str,
    source_url: str,
    settings: Settings,
    overrides: dict[str, Override] | None = None,
) -> dict:
    extraction = extract_elements(
        title=title,
        content=content,
        source_url=source_url,
        overrides=overrides,
    )

    rows = [{"label": lbl, "id": ELEMENTS[lbl]} for lbl in sorted(extraction.evidence.keys())]
    elements_table = pd.DataFrame(rows)

    client = RaisonClient(settings)
    decision = client.solve(sorted(list(extraction.element_ids)))

    return {
        "elements_table": elements_table,
        "evidence": extraction.evidence,
        "decision_label": decision.chosen_option_label,
        "decision_id": decision.chosen_option_id,
        "explanations": decision.explanations,
        "raw_raison": decision.raw,
    }