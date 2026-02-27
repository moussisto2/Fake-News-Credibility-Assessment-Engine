from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from fnce.config import Settings
from fnce.core.schema import SOLUTION_PRIORITY, ELEMENTS


@dataclass
class RaisonDecision:
    chosen_option_label: str
    chosen_option_id: str
    explanations: list[str]
    raw: Any


class RaisonClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.settings.raison_api_key,
            "accept": "application/json",
            "content-type": "application/json",
        }

    def solve(self, element_ids: list[str]) -> RaisonDecision:
        url = self.settings.raison_execution_url

        payload = {
            "elements": [{"id": eid} for eid in element_ids],
            "options": [
                {"id": "OPT389268"},  # credible
                {"id": "OPT389318"},  # needs_verification
                {"id": "OPT389368"},  # likely_misinformation
            ],
            "limit": 10,
        }

        resp = requests.post(
            url,
            headers=self._headers(),
            json=payload,
            timeout=self.settings.raison_timeout_seconds,
        )

        if resp.status_code >= 400:
            raise RuntimeError(f"RAISON error {resp.status_code}: {resp.text}")

        data = resp.json()

        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected RAISON response type: {type(data)}")

        # ================================
        # 🔥 DEMO OVERRIDE LOGIC
        # If reputable_source is present → FORCE credible
        # ================================
        reputable_id = ELEMENTS.get("reputable_source")

        if reputable_id in element_ids:
            return RaisonDecision(
                chosen_option_label="credible",
                chosen_option_id="OPT389268",
                explanations=[
                    "credible is selected because reputable_source is present (demo rule override)"
                ],
                raw=data,
            )

        # ================================
        # NORMAL RAISON BEHAVIOR
        # ================================

        solutions = [x for x in data if isinstance(x, dict) and x.get("isSolution") is True]

        if not solutions:
            solutions = [x for x in data if isinstance(x, dict) and "option" in x]

        chosen = self._choose_solution(solutions)

        option = (chosen.get("option") or {}) if isinstance(chosen, dict) else {}
        chosen_label = option.get("label", "unknown")
        chosen_id = option.get("id", "unknown")

        merged: list[str] = []

        def add_expl(obj: dict[str, Any]) -> None:
            expl = obj.get("explanation")
            if isinstance(expl, list):
                for line in expl:
                    line = str(line).strip()
                    if line and line not in merged:
                        merged.append(line)
            elif isinstance(expl, str):
                line = expl.strip()
                if line and line not in merged:
                    merged.append(line)

        if isinstance(chosen, dict):
            add_expl(chosen)

        for s in solutions:
            if isinstance(s, dict) and s is not chosen:
                add_expl(s)

        return RaisonDecision(
            chosen_option_label=str(chosen_label),
            chosen_option_id=str(chosen_id),
            explanations=merged,
            raw=data,
        )

    def _choose_solution(self, solutions: list[dict[str, Any]]) -> dict[str, Any]:
        by_label: dict[str, dict[str, Any]] = {}
        for s in solutions:
            opt = s.get("option") or {}
            label = opt.get("label")
            if isinstance(label, str) and label not in by_label:
                by_label[label] = s

        for label in SOLUTION_PRIORITY:
            if label in by_label:
                return by_label[label]

        return solutions[0] if solutions else {}