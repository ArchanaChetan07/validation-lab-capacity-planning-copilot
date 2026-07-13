"""Domain-model-driven discrete-event scheduling simulation (v2).

Unlike engine.py's walking-skeleton uniform-pool model, this version uses
the real domain model: heterogeneous racks (compatibility per suite),
named license pools (per-suite requirement), per-suite runtime
distributions, and a priority/preemption policy.

Kept as a separate module (`engine_v2`) alongside the original so the
existing API slice keeps working while this is validated; the API will be
switched over once scenario construction (Phase 5) exercises it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import simpy

from capacity_copilot.models.rack import RackInventory
from capacity_copilot.models.license_pool import LicenseRegistry
from capacity_copilot.models.test_suite import TestSuite, RegressionCampaign
from capacity_copilot.models.priority_policy import PriorityPolicy, PriorityTier


@dataclass
class JobTrace:
    category: str
    tier: PriorityTier
    start_time: float
    finish_time: float


@dataclass
class SimResultV2:
    completion_time_hours: float
    per_suite_completion: dict[str, float]
    rack_busy_hours: float
    license_busy_hours: dict[str, float]
    traces: list[JobTrace] = field(default_factory=list)


def _build_rack_resources(env: simpy.Environment, inventory: RackInventory):
    """One simpy.PriorityResource per compatible-suite-set 'pool' is overkill for v1;
    instead we model racks as a single pooled PriorityResource per rack TYPE, and check
    suite compatibility before requesting. This keeps v1 tractable while still
    respecting heterogeneity."""
    resources: dict[str, simpy.PriorityResource] = {}
    racks_by_type: dict[str, int] = {}
    for rack in inventory.racks:
        racks_by_type[rack.rack_type.value] = racks_by_type.get(rack.rack_type.value, 0) + 1
    for rack_type, count in racks_by_type.items():
        resources[rack_type] = simpy.PriorityResource(env, capacity=count)
    return resources


def run_campaign_simulation(
    campaign: RegressionCampaign,
    suites: dict[str, TestSuite],
    rack_inventory: RackInventory,
    license_registry: LicenseRegistry,
    priority_policy: PriorityPolicy,
    job_tier: PriorityTier = PriorityTier.STANDARD,
    seed: int = 0,
) -> SimResultV2:
    """Run a single trial of the full campaign through the domain model."""
    rng = np.random.default_rng(seed)
    env = simpy.Environment()

    rack_resources = _build_rack_resources(env, rack_inventory)
    # license seats modeled as simpy.Resource per named pool
    license_resources = {
        name: simpy.Resource(env, capacity=pool.total_seats)
        for name, pool in license_registry.pools.items()
    }

    traces: list[JobTrace] = []

    def run_job(suite: TestSuite, runtime_hours: float, tier: PriorityTier):
        # pick the first rack type this suite is compatible with that has a resource.
        # sorted() for determinism: iterating a set directly has no guaranteed order
        # and can vary between runs/processes, which would make "seed"-based
        # reproducibility unreliable for multi-rack-type suites.
        compatible_types = sorted(
            rt for rt in suite.compatible_rack_types if rt in rack_resources
        ) or sorted(rack_resources.keys())  # fallback: any rack if unspecified
        rack_res = rack_resources[compatible_types[0]]

        lic_res = license_resources.get(suite.required_license) if suite.required_license else None

        # Request the license first (often the scarcer resource) so the rack is only
        # held for the actual test duration, not while queued behind a license seat.
        if lic_res is not None:
            with lic_res.request() as lic_req:
                yield lic_req
                with rack_res.request(priority=int(tier)) as rack_req:
                    yield rack_req
                    start = env.now
                    yield env.timeout(runtime_hours)
        else:
            with rack_res.request(priority=int(tier)) as rack_req:
                yield rack_req
                start = env.now
                yield env.timeout(runtime_hours)
        traces.append(JobTrace(category=suite.category, tier=tier,
                                start_time=start, finish_time=env.now))

    for category, count in campaign.suite_counts.items():
        suite = suites[category]
        runtimes = suite.sample_runtime_hours(rng, n=count)
        for rt in runtimes:
            env.process(run_job(suite, float(rt), job_tier))

    env.run()

    completion_time = max((t.finish_time for t in traces), default=0.0)
    per_suite_completion: dict[str, float] = {}
    for t in traces:
        per_suite_completion[t.category] = max(per_suite_completion.get(t.category, 0.0), t.finish_time)

    rack_busy_hours = sum(t.finish_time - t.start_time for t in traces)
    license_busy_hours: dict[str, float] = {}
    for t in traces:
        suite = suites[t.category]
        if suite.required_license:
            license_busy_hours[suite.required_license] = (
                license_busy_hours.get(suite.required_license, 0.0) + (t.finish_time - t.start_time)
            )

    return SimResultV2(
        completion_time_hours=completion_time,
        per_suite_completion=per_suite_completion,
        rack_busy_hours=rack_busy_hours,
        license_busy_hours=license_busy_hours,
        traces=traces,
    )


def monte_carlo(
    campaign: RegressionCampaign,
    suites: dict[str, TestSuite],
    rack_inventory: RackInventory,
    license_registry: LicenseRegistry,
    priority_policy: PriorityPolicy,
    trials: int = 20,
) -> list[SimResultV2]:
    return [
        run_campaign_simulation(
            campaign, suites, rack_inventory, license_registry, priority_policy, seed=i
        )
        for i in range(trials)
    ]
