from __future__ import annotations

import responses

from fnce.config import Settings
from fnce.core.raison_client import RaisonClient


def make_settings() -> Settings:
    return Settings(
        raison_api_key="test-key",
        raison_base_url="https://api.ai-raison.com",
        raison_metadata_path="/v1/projects/PRJ29925/metadata",
        raison_solve_path="/v1/projects/PRJ29925/solve",
        raison_timeout_seconds=5,
        app_debug=True,
    )


@responses.activate
def test_solve_payload_sends_element_ids_only_and_has_api_key_header():
    settings = make_settings()
    client = RaisonClient(settings)

    responses.add(
        responses.POST,
        settings.solve_url,
        json=[
            {
                "option": {"label": "credible", "id": "OPT389268"},
                "explanation": ["credible is a solution because has_verifiable_source."],
                "isSolution": True,
            }
        ],
        status=200,
    )

    element_ids = ["OPT389218", "OPT389418"]
    out = client.solve(element_ids)

    assert out.chosen_option_label == "credible"

    assert len(responses.calls) == 1
    req = responses.calls[0].request

    assert req.headers.get("x-api-key") == "test-key"

    body = req.body.decode("utf-8") if isinstance(req.body, (bytes, bytearray)) else str(req.body)
    assert "OPT389218" in body and "OPT389418" in body
    assert '"elements"' in body
