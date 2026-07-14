![CI](https://github.com/ArchanaChetan07/validation-lab-capacity-planning-copilot/actions/workflows/ci.yml/badge.svg)

Monte Carlo capacity planner for chip-validation labs — SimPy simulation, FastAPI, Anthropic-powered bottleneck explanations, Prometheus metrics.

P90 wait time cut up to **65.2%** (A1: 3.27h → 1.14h; also B3 63.1%, C1 12.9%) across license / rack / suite bottlenecks — **13/13** known-answer scenarios pass; **27/27** pytest.

How to run: `docker compose up` → open `http://localhost:8000` (chat UI), `POST /ask`, `GET /metrics`.

---

## Overview

FPGA / emulation **validation labs** often mis-buy license seats or racks because queueing contention is hard to see until schedules slip. This copilot turns a parameterized lab into a **SimPy Monte Carlo** campaign, diagnoses the binding constraint (license seats, rack count, or a dominant slow suite), and re-simulates the recommended fix so every percentage is grounded in simulation — not LLM invention.

Optional Anthropic calls only **explain** numbers the simulator already computed ([`LIMITATIONS.md`](LIMITATIONS.md)).

> All numbers below were re-run in this repo from `scripts/run_validation.py` (25 trials / scenario). Scenarios are **fully synthetic** — no employer or production lab data.

---

## Problem

In a chip-validation lab, tests compete for:

- **EDA / DFT license seats** — a scarce software pool many jobs must hold
- **FPGA / prototype racks** — physical benches compatible with particular suites
- **Suite mix** — a few long-running suites can dominate wall-clock even when capacity looks adequate

Buying more of the wrong resource wastes budget. The copilot answers: *what is binding queue time today, and how much P90 completion time drops if we relieve it?*

---

## Method

1. Load YAML / programmatic scenarios with one **injected ground-truth** bottleneck (license-, rack-, or suite-bound).
2. Run **Monte Carlo discrete-event simulation** (`sim/engine_v2`) — NumPy-sampled runtimes, SimPy contention on licenses then racks.
3. **Sensitivity analysis** (`diagnose`) perturbs seats, racks, or dominant-suite mean runtime.
4. Report binding constraint + **before/after P90 hours** and `%` improvement; re-sim confirms the fix.
5. Serve via **FastAPI** (`/ask`); emit **Prometheus** at `/metrics`; optional Anthropic narration.

Trial scaling for API latency: `trials = 15` if `test_count ≤ 2000`, else `8` / `5` for larger campaigns.

---

## Results

| Metric | Value |
|--------|--------|
| Diagnosis accuracy | **13/13** injected bottlenecks correctly identified |
| Recommendation validity | **13/13** re-sims lowered P90 completion time |
| Strongest P90 cut | **A1 / A3 / B1: 65.2%** |
| Pytest | **27/27** (includes mocked Anthropic `/ask` + `/metrics`) |

### Full known-answer table (re-verified)

| Scenario | Known bottleneck | Diagnosed | Baseline P90 (h) | After fix P90 (h) | Improvement |
|----------|------------------|-----------|-----------------:|------------------:|------------:|
| A1_license_bound | license_seats | license_seats:dft_tool | 3.27 | 1.14 | **65.2%** |
| A2_license_bound | license_seats | license_seats:dft_tool | 2.14 | 1.12 | 47.5% |
| A3_license_bound | license_seats | license_seats:dft_tool | 2.76 | 0.96 | **65.2%** |
| A4_license_bound | license_seats | license_seats:dft_tool | 3.20 | 1.69 | 47.2% |
| A5_license_bound | license_seats | license_seats:dft_tool | 2.83 | 1.73 | 39.0% |
| B1_rack_bound | rack_count | rack_count:fpga_prototype | 3.27 | 1.14 | **65.2%** |
| B2_rack_bound | rack_count | rack_count:fpga_prototype | 2.14 | 1.12 | 47.5% |
| B3_rack_bound | rack_count | rack_count:fpga_prototype | 2.21 | 0.81 | **63.1%** |
| B4_rack_bound | rack_count | rack_count:fpga_prototype | 2.16 | 1.38 | 36.1% |
| C1_dominant_suite_bound | dominant_suite | dominant_suite:slow_suite | 6.06 | 5.28 | **12.9%** |
| C2_dominant_suite_bound | dominant_suite | dominant_suite:slow_suite | 4.88 | 4.27 | 12.5% |
| C3_dominant_suite_bound | dominant_suite | dominant_suite:slow_suite | 7.59 | 6.60 | 13.1% |
| C4_dominant_suite_bound | dominant_suite | dominant_suite:slow_suite | 4.71 | 4.10 | 13.0% |

Exemplar shapes: **A1** = 1 `dft_tool` seat · 20 racks · 30 tests; **B3** = 1 rack · 25 seats · 20 tests; **C1** = 200×4min + 10×150min with adequate capacity. Full write-up: [`VALIDATION_REPORT.md`](VALIDATION_REPORT.md).

---

## How to Run

```bash
git clone https://github.com/ArchanaChetan07/validation-lab-capacity-planning-copilot.git
cd validation-lab-capacity-planning-copilot

# Preferred
docker compose up --build
# UI http://localhost:8000  ·  POST /ask  ·  GET /metrics  ·  GET /health

# Local (no Docker)
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export PYTHONPATH=src
uvicorn capacity_copilot.api.main:app --reload
```

Optional: set `ANTHROPIC_API_KEY` for LLM explanations. Without it, `/ask` still returns grounded simulation numbers with a clear reasoner fallback. Override host port with `HOST_PORT=8011 docker compose up` if 8000 is busy.

Regenerate the results table:

```bash
PYTHONPATH=src python scripts/run_validation.py
```

---

## Tests

```bash
pytest -q
# 27 passed — engine, models, sensitivity, parser bounds, reasoner missing-key,
# and API smoke tests with Anthropic mocked (no secrets).
```

CI (`.github/workflows/ci.yml`) runs the same suite with an empty `ANTHROPIC_API_KEY`, then `scripts/run_validation.py` for the **13/13** known-answer check.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Simulation | SimPy 4.1.2, NumPy runtime sampling |
| Stats | SciPy, P90 aggregation |
| API | FastAPI, Uvicorn, Pydantic |
| Reasoning | Anthropic SDK (explanation only) |
| Observability | prometheus-client (`/metrics`) |
| Config | YAML scenarios, python-dotenv |
| Quality | pytest, GitHub Actions, Docker Compose |

Layout: `scenarios/` · `src/capacity_copilot/{sim,analysis,models,reasoning,api}` · `tests/` · `scripts/run_validation.py` · `static/index.html`.

---

## Honest scope

- **13/13** = correct ID of **synthetic** injected bottlenecks — not proof on real lab traces
- Priority/preemption is queued in SimPy but not yet a sensitivity candidate
- Dominant-suite “fix” uses a **15%** mean-runtime proxy (directional)

See [`LIMITATIONS.md`](LIMITATIONS.md) · [`DEPLOY.md`](DEPLOY.md).

---

## License

See repository license / owner terms for this project.
