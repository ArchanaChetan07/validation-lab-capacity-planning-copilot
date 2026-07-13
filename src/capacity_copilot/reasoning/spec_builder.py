"""Bridges the regex-based NL parser (parser.py) to a full ScenarioSpec so the
live API can run the real domain-model simulation (engine_v2/sensitivity_v2)
instead of the v1 uniform-pool walking skeleton.

v1 limitation carried forward: the live API only knows how to build a
single-suite scenario from free text (it doesn't yet parse multiple test-suite
categories, heterogeneous rack types, or priority tiers from natural language).
Multi-suite/heterogeneous scenarios are exercised via scenarios/definitions.py
and the validation report, not yet via the chat UI.
"""
from __future__ import annotations

from capacity_copilot.models.rack import RackInventory, Rack, RackType
from capacity_copilot.models.license_pool import LicenseRegistry, LicensePool
from capacity_copilot.models.test_suite import TestSuite, RegressionCampaign
from capacity_copilot.models.priority_policy import PriorityPolicy
from capacity_copilot.models.scenario import ScenarioSpec
from capacity_copilot.reasoning.parser import ScenarioParams


def build_default_spec(params: ScenarioParams) -> ScenarioSpec:
    inventory = RackInventory(racks=[
        Rack(rack_id=f"r{i}", rack_type=RackType.FPGA_PROTOTYPE, compatible_suites={"regression"})
        for i in range(params.rack_count)
    ])
    license_registry = LicenseRegistry()
    license_registry.add(LicensePool(name="shared_tool", total_seats=params.license_seats))
    suites = {
        "regression": TestSuite(
            category="regression",
            mean_runtime_minutes=params.avg_test_minutes,
            required_license="shared_tool",
            compatible_rack_types={RackType.FPGA_PROTOTYPE.value},
        )
    }
    campaign = RegressionCampaign(suite_counts={"regression": params.test_count})
    return ScenarioSpec(campaign, suites, inventory, license_registry, PriorityPolicy())


def summarize(params: ScenarioParams) -> str:
    return (
        f"{params.test_count} tests, {params.rack_count} racks, "
        f"{params.license_seats} license seats, deadline {params.deadline_hours} hours."
    )
