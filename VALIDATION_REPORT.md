# Validation Report

**IMPORTANT:** All scenarios below are fully synthetic and parameterized for this
project — none use real employer, lab, or test-suite data. Results are validated
against known-answer synthetic scenarios with an injected ground-truth bottleneck,
not against real-world validation-lab operations.

**Diagnosis accuracy: 13/13 scenarios correctly identified the injected bottleneck.**

| Scenario | Known Bottleneck | Diagnosed | Baseline (P90 h) | After Fix (P90 h) | Improvement | Diagnosis | Recommendation Valid |
|---|---|---|---|---|---|---|---|
| A1_license_bound | license_seats | license_seats:dft_tool | 3.27 | 1.14 | 65.2% | ✅ PASS | ✅ |
| A2_license_bound | license_seats | license_seats:dft_tool | 2.14 | 1.12 | 47.5% | ✅ PASS | ✅ |
| A3_license_bound | license_seats | license_seats:dft_tool | 2.76 | 0.96 | 65.2% | ✅ PASS | ✅ |
| A4_license_bound | license_seats | license_seats:dft_tool | 3.20 | 1.69 | 47.2% | ✅ PASS | ✅ |
| A5_license_bound | license_seats | license_seats:dft_tool | 2.83 | 1.73 | 39.0% | ✅ PASS | ✅ |
| B1_rack_bound | rack_count | rack_count:fpga_prototype | 3.27 | 1.14 | 65.2% | ✅ PASS | ✅ |
| B2_rack_bound | rack_count | rack_count:fpga_prototype | 2.14 | 1.12 | 47.5% | ✅ PASS | ✅ |
| B3_rack_bound | rack_count | rack_count:fpga_prototype | 2.21 | 0.81 | 63.1% | ✅ PASS | ✅ |
| B4_rack_bound | rack_count | rack_count:fpga_prototype | 2.16 | 1.38 | 36.1% | ✅ PASS | ✅ |
| C1_dominant_suite_bound | dominant_suite | dominant_suite:slow_suite | 6.06 | 5.28 | 12.9% | ✅ PASS | ✅ |
| C2_dominant_suite_bound | dominant_suite | dominant_suite:slow_suite | 4.88 | 4.27 | 12.5% | ✅ PASS | ✅ |
| C3_dominant_suite_bound | dominant_suite | dominant_suite:slow_suite | 7.59 | 6.60 | 13.1% | ✅ PASS | ✅ |
| C4_dominant_suite_bound | dominant_suite | dominant_suite:slow_suite | 4.71 | 4.10 | 13.0% | ✅ PASS | ✅ |

## Scenario Descriptions

- **A1_license_bound**: 20 racks (abundant), only 1 license seat(s) for 30 tests — license pool should bind regardless of rack count.
- **A2_license_bound**: 15 racks (abundant), only 2 license seat(s) for 40 tests — license pool should bind regardless of rack count.
- **A3_license_bound**: 25 racks (abundant), only 1 license seat(s) for 25 tests — license pool should bind regardless of rack count.
- **A4_license_bound**: 10 racks (abundant), only 2 license seat(s) for 60 tests — license pool should bind regardless of rack count.
- **A5_license_bound**: 30 racks (abundant), only 3 license seat(s) for 80 tests — license pool should bind regardless of rack count.
- **B1_rack_bound**: Only 1 rack(s), 20 license seats (abundant) for 30 tests — rack count should bind regardless of license seats.
- **B2_rack_bound**: Only 2 rack(s), 15 license seats (abundant) for 40 tests — rack count should bind regardless of license seats.
- **B3_rack_bound**: Only 1 rack(s), 25 license seats (abundant) for 20 tests — rack count should bind regardless of license seats.
- **B4_rack_bound**: Only 3 rack(s), 30 license seats (abundant) for 60 tests — rack count should bind regardless of license seats.
- **C1_dominant_suite_bound**: 200 fast tests (4min) + 10 slow tests (150min) with adequate racks/licenses — 'slow_suite' should dominate the critical path.
- **C2_dominant_suite_bound**: 150 fast tests (5min) + 15 slow tests (100min) with adequate racks/licenses — 'slow_suite' should dominate the critical path.
- **C3_dominant_suite_bound**: 300 fast tests (3min) + 8 slow tests (200min) with adequate racks/licenses — 'slow_suite' should dominate the critical path.
- **C4_dominant_suite_bound**: 100 fast tests (6min) + 20 slow tests (90min) with adequate racks/licenses — 'slow_suite' should dominate the critical path.

## Methodology

1. Each scenario is constructed with one deliberately injected, known-answer bottleneck
   (see `scenarios/definitions.py` and the corresponding `.yaml` sidecar files).
2. The full pipeline (Monte Carlo discrete-event simulation -> sensitivity analysis ->
   bottleneck identifier) is run against each scenario with no knowledge of the ground truth.
3. `Diagnosis` = PASS if the identified binding constraint matches the injected ground truth.
4. `Recommendation Valid` = the simulator confirms the recommended fix actually reduces
   completion time when applied (re-simulated, not just asserted).

## Known Limitations

- Perturbation search is capped to likely candidates (rack count, license seats, dominant
  suite) rather than exhaustive, per NFR-4 — priority/preemption-driven contention is not
  yet modeled as its own perturbation candidate (see LIMITATIONS.md).
- Validated only against synthetic, parameterized scenarios — no real lab data was used
  or is available for this project.