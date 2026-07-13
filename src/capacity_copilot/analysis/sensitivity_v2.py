"""Bottleneck identification (v2) via one-at-a-time constraint perturbation,
against the full domain model (engine_v2), instead of v1's uniform pools.

Per NFR-4, the perturbation search is capped to the most likely candidates
first rather than exhaustive: rack count (per rack type present), each
license pool, and the dominant slow test suite.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from capacity_copilot.models.scenario import ScenarioSpec
from capacity_copilot.sim.engine_v2 import monte_carlo, SimResultV2


@dataclass
class PerturbationResult:
    label: str
    p90_completion_hours: float


@dataclass
class BottleneckReportV2:
    baseline_p90_hours: float
    binding_constraint: str
    perturbed_p90_hours: float
    improvement_pct: float
    all_candidates: list[PerturbationResult]


def _p90(results: list[SimResultV2]) -> float:
    return float(np.percentile([r.completion_time_hours for r in results], 90))


def diagnose(spec: ScenarioSpec, trials: int = 15, extra_racks: int = 2,
             extra_seats: int = 2, suite_speedup_factor: float = 0.85) -> BottleneckReportV2:
    baseline_results = monte_carlo(
        spec.campaign, spec.suites, spec.rack_inventory,
        spec.license_registry, spec.priority_policy, trials=trials,
    )
    baseline_p90 = _p90(baseline_results)

    candidates: list[PerturbationResult] = []

    # Candidate 1: add racks, per rack type actually present in inventory
    rack_types_present = {r.rack_type for r in spec.rack_inventory.racks}
    for rack_type in rack_types_present:
        perturbed = spec.with_extra_racks(extra_racks, rack_type)
        results = monte_carlo(
            perturbed.campaign, perturbed.suites, perturbed.rack_inventory,
            perturbed.license_registry, perturbed.priority_policy, trials=trials,
        )
        candidates.append(PerturbationResult(
            label=f"rack_count:{rack_type.value}", p90_completion_hours=_p90(results),
        ))

    # Candidate 2: add seats, per license pool present
    for license_name in spec.license_registry.pools.keys():
        perturbed = spec.with_extra_license_seats(license_name, extra_seats)
        results = monte_carlo(
            perturbed.campaign, perturbed.suites, perturbed.rack_inventory,
            perturbed.license_registry, perturbed.priority_policy, trials=trials,
        )
        candidates.append(PerturbationResult(
            label=f"license_seats:{license_name}", p90_completion_hours=_p90(results),
        ))

    # Candidate 3: speed up the dominant slow suite (realistic optimization, not a
    # magic 2x — a large speedup would be confounded with resource-doubling candidates
    # above when only one suite exists, since both scale total capacity similarly)
    perturbed = spec.with_faster_dominant_suite(speedup_factor=suite_speedup_factor)
    results = monte_carlo(
        perturbed.campaign, perturbed.suites, perturbed.rack_inventory,
        perturbed.license_registry, perturbed.priority_policy, trials=trials,
    )
    candidates.append(PerturbationResult(
        label=f"dominant_suite:{spec.dominant_suite_category()}",
        p90_completion_hours=_p90(results),
    ))

    best = min(candidates, key=lambda c: c.p90_completion_hours)
    improvement_pct = (
        (baseline_p90 - best.p90_completion_hours) / baseline_p90 * 100
        if baseline_p90 > 0 else 0.0
    )

    return BottleneckReportV2(
        baseline_p90_hours=baseline_p90,
        binding_constraint=best.label,
        perturbed_p90_hours=best.p90_completion_hours,
        improvement_pct=improvement_pct,
        all_candidates=candidates,
    )
