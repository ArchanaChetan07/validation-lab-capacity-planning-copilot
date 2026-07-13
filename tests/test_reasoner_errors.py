import os
import pytest

from capacity_copilot.reasoning import reasoner


def test_missing_api_key_raises_clean_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    reasoner._client = None  # reset singleton so the missing-key path is hit
    with pytest.raises(reasoner.ReasonerError):
        reasoner.explain(
            scenario_summary="test",
            baseline_completion_hours=1.0,
            binding_constraint="license_seats",
            perturbed_completion_hours=0.5,
            improvement_pct=50.0,
        )
