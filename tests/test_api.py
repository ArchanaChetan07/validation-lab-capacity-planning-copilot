"""API smoke tests — Anthropic is always mocked; no API key required."""
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from capacity_copilot.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_metrics_exposes_prometheus_text():
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "python_gc_objects_collected_total" in body or "copilot_requests_total" in body


def test_ask_with_mocked_anthropic_returns_grounded_numbers():
    with patch(
        "capacity_copilot.api.main.explain",
        return_value="Mocked explanation: binding constraint diagnosed.",
    ) as mocked:
        r = client.post(
            "/ask",
            json={"query": "I have 20 racks, 1 license seat, and 30 DFT tests"},
        )
    assert r.status_code == 200
    data = r.json()
    assert "Mocked explanation" in data["answer"]
    assert data["completion_time_hours"] > 0
    assert data["binding_constraint"]
    assert "improvement_pct" in data
    mocked.assert_called_once()

    # /ask should increment Prometheus counters visible on /metrics
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "copilot_requests_total" in metrics.text
