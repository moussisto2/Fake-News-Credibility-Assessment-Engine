from __future__ import annotations

from fnce.core.extractor import extract_elements
from fnce.core.schema import ELEMENTS


def test_clickbait_title_triggers():
    r = extract_elements(
        title="SHOCKING!!! You won't believe what happens next!!!",
        content="",
        source_url="",
    )
    assert ELEMENTS["clickbait_title"] in r.element_ids


def test_fact_check_failed_manual_triggers():
    r = extract_elements(
        title="Any",
        content="Any",
        source_url="https://example.com",
        manual_fact_check_failed=True,
    )
    assert ELEMENTS["fact_check_failed"] in r.element_ids


def test_neutral_tone_triggers_when_no_sensational_markers():
    r = extract_elements(
        title="Local council approves new budget",
        content="The council approved the budget after discussion. The policy takes effect next month.",
        source_url="",
    )
    assert ELEMENTS["neutral_tone"] in r.element_ids
