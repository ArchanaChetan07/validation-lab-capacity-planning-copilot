# Validation Lab Capacity-Planning Copilot — Project Plan

> **Status as of this build:** Phases 1, 3, 5, and 6 are implemented and passing (18 unit
> tests, 13/13 known-answer scenarios correctly diagnosed — see `VALIDATION_REPORT.md`).
> Phase 4 (conversational layer) is live via the deployed API/chat UI but only handles
> single-suite queries (see `LIMITATIONS.md`). Phase 7 observability is partially done
> (Prometheus metrics live at `/metrics`; Grafana dashboard not yet stood up). Details below,
> checkboxes reflect actual state.

Derived from `Capacity_Planning_Copilot_Proposal.md`. This turns the proposal's milestones into a
concrete, trackable build plan with requirements, task breakdowns, and setup steps.

---

## 1. Requirements

### 1.1 Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | Accept a natural-language capacity question (e.g., "50,000 tests, 12 racks, Friday deadline") and extract structured scenario parameters |
| FR-2 | Model rack inventory: count, type, and test-suite compatibility |
| FR-3 | Model license pools: seat counts per tool/IP block, with contention |
| FR-4 | Model test runtime distributions per test-suite category (not fixed durations) |
| FR-5 | Model priority tiers and preemption rules (what gets bumped) |
| FR-6 | Model existing queue backlog at the time of the query |
| FR-7 | Run a discrete-event simulation of the scheduling scenario (SimPy) |
| FR-8 | Run Monte Carlo trials over runtime variance to produce a confidence range (P50/P90), not a single-point estimate |
| FR-9 | Run sensitivity analysis: perturb one constraint at a time (add rack, add license seat, reduce backlog) and measure completion-time delta |
| FR-10 | Identify the binding bottleneck as the constraint whose perturbation yields the largest improvement |
| FR-11 | Generate an LLM explanation of the schedule/bottleneck that cites specific simulation figures (not invented numbers) |
| FR-12 | Generate concrete, quantified recommendations (e.g., "add 2 racks → ~14% critical-path reduction") |
| FR-13 | Expose the above via a conversational API (FastAPI) reusing the LangChain pattern from AI-Infrastructure-Copilot |
| FR-14 | Emit Prometheus metrics (query latency, sim runtime, MC trial count) and a Grafana dashboard |
| FR-15 | Support 10–15 synthetic scenarios with known, injected bottlenecks for validation |
| FR-16 | Produce `VALIDATION_REPORT.md` with ground truth vs. system diagnosis vs. pass/fail per scenario |

### 1.2 Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | No real employer/lab data anywhere in code, scenarios, or docs — synthetic only |
| NFR-2 | Simulator is the sole source of quantitative truth; LLM only explains/contextualizes |
| NFR-3 | All claims in docs/reports explicitly scoped as "validated against synthetic, known-answer scenarios" |
| NFR-4 | Sensitivity analysis capped to likely candidates first (racks, licenses, dominant test suite) for compute cost control |
| NFR-5 | Reproducible: every capacity/bottleneck claim backed by a runnable simulation script |
| NFR-6 | Test coverage via pytest in CI (GitHub Actions) |

### 1.3 Technology / Dependency Requirements

| Layer | Choice | Install |
|---|---|---|
| Language | Python 3.11+ | — |
| Conversational/reasoning | LangChain | `langchain`, `langchain-anthropic` (or `langchain-openai`) |
| Simulation | SimPy | `simpy` |
| Stats/sampling | NumPy, SciPy | `numpy`, `scipy` |
| API | FastAPI + Uvicorn | `fastapi`, `uvicorn` |
| Observability | Prometheus client, Grafana (external) | `prometheus-client` |
| Testing | pytest | `pytest`, `pytest-cov` |
| CI | GitHub Actions | `.github/workflows/ci.yml` |
| Config | Pydantic | `pydantic` |
| Env/secrets | python-dotenv | `python-dotenv` |

### 1.4 What You Need Before Starting (Inputs/Access)

- [ ] An LLM API key (Anthropic or OpenAI) for the reasoning layer — set as env var, never committed
- [ ] Python 3.11+ installed locally
- [ ] GitHub repo created (public or private) with Actions enabled
- [ ] (Optional, for observability) local Prometheus + Grafana via Docker Compose
- [ ] 2–3 published references on FPGA/emulation lab operations to ground the domain model realistically (see Appendix in proposal) — no employer data

---

## 2. Repository Structure

```
capacity-copilot/
├── README.md
├── VALIDATION_REPORT.md              # generated in Phase 6
├── requirements.txt
├── .env.example
├── .github/workflows/ci.yml
├── src/
│   └── capacity_copilot/
│       ├── __init__.py
│       ├── models/                   # domain model (Phase 1)
│       │   ├── rack.py
│       │   ├── license_pool.py
│       │   ├── test_suite.py
│       │   └── priority_policy.py
│       ├── sim/                      # simulation engine (Phase 2)
│       │   ├── engine.py             # SimPy scheduler
│       │   └── monte_carlo.py
│       ├── analysis/                 # bottleneck identifier (Phase 3)
│       │   └── sensitivity.py
│       ├── reasoning/                # conversational layer (Phase 4)
│       │   ├── parser.py             # NL -> structured scenario
│       │   ├── reasoner.py           # LLM explanation/recommendations
│       │   └── prompts.py
│       ├── api/
│       │   └── main.py               # FastAPI app
│       └── observability/
│           └── metrics.py
├── scenarios/                        # synthetic scenarios (Phase 5)
│   ├── scenario_01_license_bound.yaml
│   ├── scenario_02_slow_suite.yaml
│   └── ...
├── scripts/
│   └── run_validation.py             # Phase 6 runner
└── tests/
    ├── test_models.py
    ├── test_sim.py
    ├── test_sensitivity.py
    └── test_parser.py
```

---

## 3. Phased Task Breakdown

### Phase 1 — Domain Modeling (Week 1)
- [x] Define `Rack` model: id, type, compatible test-suite categories, status
- [x] Define `LicensePool` model: tool/IP name, total seats, held seats
- [x] Define `TestSuite` model: category, runtime distribution (e.g., lognormal params), rack compatibility, license requirement
- [x] Define `PriorityPolicy` model: tiers, preemption rules
- [ ] Define `Backlog` model: pending jobs at t=0 with their priority/suite
- [x] Write unit tests for model validation (e.g., invalid seat counts, incompatible rack assignment)
- [ ] Draft a short `DOMAIN_MODEL.md` citing published lab-operations references

### Phase 2 — Simulation Engine (Weeks 2–3)
- [x] Implement SimPy resources for racks (as `simpy.Resource`/`PriorityResource`) and license seats
- [x] Implement job arrival/queueing logic respecting priority + preemption
- [x] Sample test runtimes from configured distributions per run
- [x] Implement `run_simulation(scenario) -> completion_time, per-job trace`
- [x] Implement Monte Carlo wrapper: N trials, aggregate P50/P90 completion time
- [ ] Sanity-check simple cases against an M/M/c queueing baseline
- [x] Unit + integration tests for the simulator

### Phase 3 — Bottleneck Identifier (Week 4)
- [x] Implement perturbation set: +1 rack, +1 license seat, -X% backlog, remove dominant slow suite
- [x] Re-run simulation (with fixed random seed for fair comparison) per perturbation
- [x] Rank perturbations by completion-time improvement
- [x] Report top constraint as "binding bottleneck" with quantified delta
- [x] Cap search order to likely-candidates-first per NFR-4
- [x] Tests using scenarios with a known injected bottleneck

### Phase 4 — Conversational Layer (Weeks 5–6, ~1.5 wks)
- [x] Build query parser: NL → structured scenario params (test count, rack count, deadline, constraints)
- [ ] Reuse LangChain pattern from AI-Infrastructure-Copilot for the reasoner
- [x] Constrain LLM prompt to cite simulation figures only — no invented numbers (NFR-2)
- [x] Draft explanation + recommendation templates
- [x] Wire up FastAPI endpoint(s): `/ask`, `/scenario/{id}/diagnose`
- [ ] Tests for parser edge cases (ambiguous/missing params)

### Phase 5 — Scenario Construction (Week 7)
- [x] Build 10–15 synthetic scenarios, each with one deliberately injected bottleneck: (13 built, see `scenarios/definitions.py`)
  - Scenario type A: rack-abundant, license-scarce
  - Scenario type B: capacity-adequate except one dominant slow test suite
  - Scenario type C: priority-preemption-driven contention despite adequate capacity
- [x] Store each as YAML/JSON with documented ground-truth bottleneck
- [ ] Peer/self-review scenarios for realism vs. published literature

### Phase 6 — Evaluation (Week 8)
- [x] Run full pipeline (sim → bottleneck identifier → LLM explanation) across all scenarios
- [x] Score diagnosis accuracy vs. known ground truth
- [x] Apply top recommendation in a follow-up sim to confirm it actually improves completion time
- [x] Generate `VALIDATION_REPORT.md` with scenario table, ground truth, diagnosis, pass/fail

### Phase 7 — Observability + Final Report (Week 8.5)
- [x] Instrument query latency, sim runtime, MC trial count via `prometheus-client`
- [ ] Stand up Grafana dashboard (reuse existing panel patterns if available)
- [ ] Finalize README with explicit synthetic-data-only disclaimer
- [ ] Tag v1 release; publish validation report

---

## 4. Suggested Immediate Next Steps (This Week)

1. Create the GitHub repo and push the scaffold below.
2. Set up a virtualenv and install `requirements.txt`.
3. Write `models/rack.py`, `models/license_pool.py`, `models/test_suite.py` first — everything else depends on these.
4. Write 2–3 unit tests per model before moving to simulation (keeps Phase 2 honest).

---

## 5. Risks Carried Forward (from proposal, unchanged)

- No real lab data → mitigated by explicit synthetic scoping
- LLM inventing numbers → mitigated by architectural separation (sim computes, LLM explains)
- DES not capturing real quirks → documented as limitation, framed as planning aid
- Sensitivity analysis cost → capped perturbation search
- Overclaiming → every doc states synthetic-validation-only
