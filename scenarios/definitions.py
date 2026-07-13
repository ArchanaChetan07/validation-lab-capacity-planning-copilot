"""Synthetic validation scenarios, each with a deliberately injected, known
ground-truth bottleneck (per PROJECT_PLAN.md Phase 5 / proposal Section 7).

None of this is real lab data — every number here is invented for testing
purposes. Three families, matching the proposal's examples:
  A. rack-abundant, license-scarce      -> ground truth: license_seats
  B. capacity-adequate, one slow suite  -> ground truth: dominant_suite
  C. priority-preemption contention     -> ground truth: license_seats or
                                            rack_count depending on setup
     (priority contention isn't yet a distinct perturbation candidate in
     sensitivity_v2 — see LIMITATIONS.md; scored against the resource that
     actually binds once preemption is modeled)
"""
from __future__ import annotations

from dataclasses import dataclass

from capacity_copilot.models.rack import Rack, RackInventory, RackType
from capacity_copilot.models.license_pool import LicensePool, LicenseRegistry
from capacity_copilot.models.test_suite import TestSuite, RegressionCampaign
from capacity_copilot.models.priority_policy import PriorityPolicy
from capacity_copilot.models.scenario import ScenarioSpec


@dataclass
class NamedScenario:
    name: str
    description: str
    known_bottleneck_prefix: str  # e.g. "license_seats" or "rack_count" or "dominant_suite"
    spec: ScenarioSpec


def _racks(n: int, rack_type: RackType, suites: set[str], prefix: str = "r") -> RackInventory:
    return RackInventory(racks=[
        Rack(rack_id=f"{prefix}{i}", rack_type=rack_type, compatible_suites=suites)
        for i in range(n)
    ])


def _single_suite_spec(rack_count, license_seats, test_count, mean_minutes=6,
                        rack_type=RackType.FPGA_PROTOTYPE, suite_name="dft") -> ScenarioSpec:
    inventory = _racks(rack_count, rack_type, {suite_name})
    lic = LicenseRegistry()
    lic.add(LicensePool(name=f"{suite_name}_tool", total_seats=license_seats))
    suites = {
        suite_name: TestSuite(
            category=suite_name, mean_runtime_minutes=mean_minutes,
            required_license=f"{suite_name}_tool",
            compatible_rack_types={rack_type.value},
        )
    }
    campaign = RegressionCampaign(suite_counts={suite_name: test_count})
    return ScenarioSpec(campaign, suites, inventory, lic, PriorityPolicy())


def build_scenarios() -> list[NamedScenario]:
    scenarios: list[NamedScenario] = []

    # --- Family A: license-bound (5 variants) ---
    for i, (racks, seats, tests) in enumerate([
        (20, 1, 30), (15, 2, 40), (25, 1, 25), (10, 2, 60), (30, 3, 80),
    ], start=1):
        spec = _single_suite_spec(racks, seats, tests)
        scenarios.append(NamedScenario(
            name=f"A{i}_license_bound",
            description=f"{racks} racks (abundant), only {seats} license seat(s) for {tests} tests — "
                        f"license pool should bind regardless of rack count.",
            known_bottleneck_prefix="license_seats",
            spec=spec,
        ))

    # --- Family B: rack-bound (4 variants) ---
    for i, (racks, seats, tests) in enumerate([
        (1, 20, 30), (2, 15, 40), (1, 25, 20), (3, 30, 60),
    ], start=1):
        spec = _single_suite_spec(racks, seats, tests)
        scenarios.append(NamedScenario(
            name=f"B{i}_rack_bound",
            description=f"Only {racks} rack(s), {seats} license seats (abundant) for {tests} tests — "
                        f"rack count should bind regardless of license seats.",
            known_bottleneck_prefix="rack_count",
            spec=spec,
        ))

    # --- Family C: dominant slow-suite bound (4 variants) ---
    # Adequate racks and licenses for both suites; one suite's total workload dominates.
    for i, (fast_count, fast_min, slow_count, slow_min) in enumerate([
        (200, 4, 10, 150),
        (150, 5, 15, 100),
        (300, 3, 8, 200),
        (100, 6, 20, 90),
    ], start=1):
        inventory = _racks(15, RackType.FPGA_PROTOTYPE, {"fast_suite", "slow_suite"})
        lic = LicenseRegistry()
        lic.add(LicensePool(name="shared_tool", total_seats=15))
        suites = {
            "fast_suite": TestSuite(category="fast_suite", mean_runtime_minutes=fast_min,
                                     required_license="shared_tool",
                                     compatible_rack_types={RackType.FPGA_PROTOTYPE.value}),
            "slow_suite": TestSuite(category="slow_suite", mean_runtime_minutes=slow_min,
                                     required_license="shared_tool",
                                     compatible_rack_types={RackType.FPGA_PROTOTYPE.value}),
        }
        campaign = RegressionCampaign(suite_counts={"fast_suite": fast_count, "slow_suite": slow_count})
        spec = ScenarioSpec(campaign, suites, inventory, lic, PriorityPolicy())
        scenarios.append(NamedScenario(
            name=f"C{i}_dominant_suite_bound",
            description=f"{fast_count} fast tests ({fast_min}min) + {slow_count} slow tests ({slow_min}min) "
                        f"with adequate racks/licenses — 'slow_suite' should dominate the critical path.",
            known_bottleneck_prefix="dominant_suite",
            spec=spec,
        ))

    return scenarios
