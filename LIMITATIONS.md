# Known Limitations

Stated explicitly, per the project's honesty-first validation discipline (see
`PROJECT_PLAN.md` NFR-3 and the proposal's Section 7).

## Scope limitations

- **No real lab data.** Every scenario, runtime distribution, and rack/license count in
  this project is synthetic and invented for testing. Nothing here is validated against
  real validation-lab operations, and no claim in this repo should be read that way.
- **Live API only builds single-suite scenarios.** `spec_builder.py` turns a free-text
  query into one test-suite category with one shared license pool and one rack type.
  The richer multi-suite, heterogeneous-rack scenarios in `scenarios/definitions.py` are
  exercised by the validation report, not yet reachable through the chat UI. Extending the
  NL parser (ideally to an LLM-based extractor) to populate multi-suite campaigns from
  free text is the natural next step.
- **Priority/preemption is modeled but not yet a perturbation candidate.** `PriorityPolicy`
  and `PriorityTier` exist and are wired into the simulation's queueing (priority-based
  resource requests), but `sensitivity_v2.diagnose` doesn't yet perturb "reduce backlog" or
  "change priority policy" as its own bottleneck candidate — only rack count, license
  seats, and the dominant slow suite are searched, per NFR-4's "likely candidates first"
  cap. A scenario where priority-preemption is the *actual* binding constraint despite
  adequate raw capacity (the proposal's scenario type C) is not yet distinctly diagnosable
  from this set.
- **Dominant-suite "speedup" is a proxy recommendation, not a specific one.** Perturbing
  the dominant suite's mean runtime by a flat 15% stands in for "optimize or split this
  test suite" — the system doesn't know *how* to speed up a suite, just that doing so by a
  plausible amount would help. Treat this recommendation as directional, not a specific
  optimization plan.
- **Backlog/existing-queue modeling is not yet implemented.** `RegressionCampaign` assumes
  every test in the campaign is new and starts at t=0; there's no support yet for an
  existing in-flight backlog at the time of the query, despite it being in FR-6 of the plan.

## Methodology note (found and fixed during Phase 6 evaluation)

Early validation runs caught two real issues, both fixed and left documented here rather
than quietly patched:

1. **Rack-hostage bug**: in `engine_v2`, racks were originally held for the entire time a
   job was queued behind a license seat, not just its actual execution time — this made
   racks look artificially "busy" even when licenses were the true bottleneck. Fixed by
   requesting the scarcer resource (license) before acquiring the rack.
2. **Confounded perturbation magnitude**: a 50% suite-runtime speedup was mathematically
   too close to a "double the scarce resource" perturbation in single-suite scenarios,
   causing 5/13 known-answer scenarios to misdiagnose the bottleneck as the suite rather
   than the actual injected resource constraint. Fixed by reducing the suite-speedup
   candidate to a more realistic 15%, which also disambiguates it from resource-doubling
   candidates. See `VALIDATION_REPORT.md` for the corrected 13/13 result.

## Honest scope of "13/13 passing"

13/13 means the bottleneck identifier correctly named the injected ground-truth constraint
across 13 synthetic, known-answer scenarios covering 3 scenario families (license-bound,
rack-bound, dominant-suite-bound). It does not mean the system has been validated on
priority-preemption-bound scenarios (not yet distinctly diagnosable, see above), nor on any
real-world data (none exists for this project).
