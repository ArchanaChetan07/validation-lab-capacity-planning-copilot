"""Bundles a full scenario's domain-model inputs together, and provides
copy-with-perturbation helpers used by the sensitivity/bottleneck analysis.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass

from capacity_copilot.models.rack import Rack, RackInventory, RackType
from capacity_copilot.models.license_pool import LicenseRegistry
from capacity_copilot.models.test_suite import TestSuite, RegressionCampaign
from capacity_copilot.models.priority_policy import PriorityPolicy


@dataclass
class ScenarioSpec:
    campaign: RegressionCampaign
    suites: dict[str, TestSuite]
    rack_inventory: RackInventory
    license_registry: LicenseRegistry
    priority_policy: PriorityPolicy

    def with_extra_racks(self, count: int, rack_type: RackType) -> "ScenarioSpec":
        """Return a copy with `count` additional racks of the given type,
        compatible with every suite currently compatible with that type."""
        new_spec = copy.deepcopy(self)
        # infer which suite categories this rack type currently serves
        served_categories = {
            suite.category
            for suite in self.suites.values()
            if rack_type.value in suite.compatible_rack_types
        }
        existing_ids = {r.rack_id for r in new_spec.rack_inventory.racks}
        i = 0
        added = 0
        while added < count:
            candidate_id = f"extra-{rack_type.value}-{i}"
            i += 1
            if candidate_id in existing_ids:
                continue
            new_spec.rack_inventory.racks.append(
                Rack(rack_id=candidate_id, rack_type=rack_type, compatible_suites=served_categories)
            )
            added += 1
        return new_spec

    def with_extra_license_seats(self, license_name: str, count: int) -> "ScenarioSpec":
        new_spec = copy.deepcopy(self)
        pool = new_spec.license_registry.pools[license_name]
        pool.total_seats += count
        return new_spec

    def dominant_suite_category(self) -> str:
        """The suite category with the highest mean_runtime * count product —
        the best candidate for 'the one slow test suite that dominates'."""
        def work(category: str) -> float:
            count = self.campaign.suite_counts.get(category, 0)
            return count * self.suites[category].mean_runtime_minutes

        return max(self.suites.keys(), key=work)

    def with_faster_dominant_suite(self, speedup_factor: float = 0.5) -> "ScenarioSpec":
        """Return a copy where the dominant suite's mean runtime is reduced —
        simulates splitting/optimizing the slow suite."""
        new_spec = copy.deepcopy(self)
        dominant = self.dominant_suite_category()
        new_spec.suites[dominant].mean_runtime_minutes *= speedup_factor
        return new_spec
