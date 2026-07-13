# Validation Lab Capacity-Planning Copilot

A conversational capacity-planning assistant for hardware validation labs. Ask a
question like *"50000 tests, 12 racks, 4 license seats, deadline 96 hours"* and it
runs a real Monte Carlo discrete-event simulation, identifies which resource is
actually binding your schedule (racks, license seats, or a slow test suite), and
explains the result in plain language — grounded entirely in the simulator's own
numbers, never invented.

**Status: feature-complete, hardened, and tested.** 24/24 unit tests passing,
13/13 known-answer validation scenarios correctly diagnosed, all critical/high
bugs found in the production audit fixed. See the docs map below for details on
each part.

> **All data in this project — scenarios, runtimes, rack/license counts — is
> synthetic and invented for testing. No real employer or lab data is used
> anywhere.**

---

## Quick start

```bash
git clone <this-repo>
cd capacity-copilot
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
PYTHONPATH=src uvicorn capacity_copilot.api.main:app --reload
```
Open **http://localhost:8000** — the diagnosis console UI is there.

Run the tests:
```bash
PYTHONPATH=src python3 -m pytest tests/ -q
```

Run the full known-answer validation suite:
```bash
PYTHONPATH=src python3 scripts/run_validation.py
```

Deploy it live (Railway/Render/Fly.io, ~5 minutes) — see **[DEPLOY.md](DEPLOY.md)**.

---

## How it works

```
"50000 tests, 12 racks,      →  parser.py           →  structured ScenarioParams
 4 license seats, 96h"

ScenarioParams                →  spec_builder.py     →  full domain-model ScenarioSpec
                                                          (racks, license pools,
                                                           test suites, priority policy)

ScenarioSpec                  →  engine_v2.py         →  SimPy discrete-event simulation
                                  (Monte Carlo, N trials)   → P90 completion time

ScenarioSpec + baseline       →  sensitivity_v2.py    →  perturb rack count, license
                                                          seats, dominant suite one at
                                                          a time → binding constraint +
                                                          quantified improvement

Grounded numbers only         →  reasoner.py          →  LLM explains the diagnosis in
(NFR-2: no invented figures)                              plain language
```

Every number the LLM is allowed to talk about is computed by the simulator first
— the LLM explains and recommends, it never estimates completion times or
bottlenecks itself.

---

## Project layout

```
capacity-copilot/
├── README.md                 ← you are here
├── PROJECT_PLAN.md           ← requirements + phased build plan, with completion status
├── VALIDATION_REPORT.md      ← 13/13 known-answer scenario results
├── LIMITATIONS.md            ← honest scope: what this does NOT do yet
├── DEPLOY.md                 ← deployment guide + full production-hardening changelog
├── requirements.txt          ← pinned exact dependency versions
├── Dockerfile / Procfile / railway.json   ← deploy configs
├── .github/workflows/ci.yml  ← CI: installs deps, runs pytest on every push
│
├── src/capacity_copilot/
│   ├── models/                ← domain model: Rack, LicensePool, TestSuite,
│   │                             PriorityPolicy, ScenarioSpec (bundles them + perturbation helpers)
│   ├── sim/engine_v2.py       ← SimPy discrete-event + Monte Carlo simulation
│   ├── analysis/sensitivity_v2.py  ← bottleneck identification via perturbation
│   ├── reasoning/
│   │   ├── parser.py          ← NL → structured params, with input bounds/clamping
│   │   ├── spec_builder.py    ← params → full ScenarioSpec (live API's default case)
│   │   └── reasoner.py        ← LLM explanation layer, error-handled
│   ├── api/main.py            ← FastAPI app: /ask, /health, /ready, /metrics
│   └── observability/         ← (Prometheus metrics wired directly into api/main.py)
│
├── static/index.html          ← the chat UI ("diagnosis console")
├── scenarios/                 ← 13 synthetic known-answer validation scenarios
│   ├── definitions.py         ← source of truth (Python objects)
│   ├── *.yaml                 ← human-readable export of each scenario
│   └── export_yaml.py         ← regenerates the YAML files from definitions.py
├── scripts/run_validation.py  ← runs all scenarios, writes VALIDATION_REPORT.md
└── tests/                     ← 24 unit/integration tests
```

---

## What's implemented vs. what's scoped out

**Implemented and tested:**
- Full domain model (heterogeneous racks, named license pools, per-suite runtime
  distributions, priority/preemption policy)
- Monte Carlo discrete-event simulation (SimPy)
- Bottleneck identification via one-at-a-time perturbation (racks, license seats,
  dominant slow suite), capped to likely candidates for compute cost
- LLM explanation layer, architecturally constrained to only cite real sim numbers
- Live API + chat UI, wired to the real domain-model pipeline (not a stand-in)
- 13 synthetic known-answer scenarios, 13/13 correctly diagnosed
- Production hardening: input bounds, error handling, no stack-trace leaks,
  optional auth, non-root Docker, pinned dependencies (see DEPLOY.md for the
  full list of what was found and fixed in the audit)

**Explicitly out of scope for this build** (see LIMITATIONS.md for detail):
- The live chat UI only builds single-suite scenarios from free text; multi-suite
  campaigns are exercised via `scenarios/definitions.py`, not the chat UI yet
- Priority/preemption contention isn't yet its own diagnosable bottleneck candidate
- No backlog/existing-queue modeling
- No rate limiting beyond the hosting platform's own defaults
- Grafana dashboard isn't stood up (Prometheus metrics are live at `/metrics`;
  point your own Grafana/Grafana Cloud at it)

---

## Documentation map

| Doc | What's in it |
|---|---|
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | Original requirements (functional/non-functional), phased task breakdown, completion status |
| [VALIDATION_REPORT.md](VALIDATION_REPORT.md) | Full scenario-by-scenario diagnosis accuracy table + methodology |
| [LIMITATIONS.md](LIMITATIONS.md) | Honest scope statement, including two real bugs found and fixed during evaluation |
| [DEPLOY.md](DEPLOY.md) | Deploy steps for Railway/Render/Fly.io + full production-hardening changelog (10 issues found and fixed) |
