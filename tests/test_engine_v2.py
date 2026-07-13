import numpy as np

from capacity_copilot.models.rack import Rack, RackInventory, RackType
from capacity_copilot.models.license_pool import LicensePool, LicenseRegistry
from capacity_copilot.models.test_suite import TestSuite, RegressionCampaign
from capacity_copilot.models.priority_policy import PriorityPolicy
from capacity_copilot.sim.engine_v2 import run_campaign_simulation, monte_carlo


def _abundant_racks_scarce_license_scenario():
    """Known-answer scenario: plenty of racks, only 1 license seat.
    Ground truth: the license pool should be the binding constraint."""
    inventory = RackInventory(racks=[
        Rack(rack_id=f"r{i}", rack_type=RackType.FPGA_PROTOTYPE, compatible_suites={"dft"})
        for i in range(20)
    ])
    license_registry = LicenseRegistry()
    license_registry.add(LicensePool(name="dft_tool", total_seats=1))

    suites = {
        "dft": TestSuite(
            category="dft",
            mean_runtime_minutes=6,
            required_license="dft_tool",
            compatible_rack_types={RackType.FPGA_PROTOTYPE.value},
        )
    }
    campaign = RegressionCampaign(suite_counts={"dft": 50})
    return campaign, suites, inventory, license_registry, PriorityPolicy()


def test_license_bottleneck_serializes_despite_many_racks():
    campaign, suites, inventory, licenses, policy = _abundant_racks_scarce_license_scenario()
    result = run_campaign_simulation(campaign, suites, inventory, licenses, policy, seed=1)

    # With only 1 license seat, jobs cannot run in parallel regardless of 20 racks,
    # so completion time should be close to serial execution: 50 * mean_runtime.
    expected_serial_hours = 50 * (6 / 60)
    assert result.completion_time_hours >= expected_serial_hours * 0.7

    # Rack busy-hours should be far less than completion_time * rack_count,
    # proving racks are NOT the bottleneck (mostly idle).
    assert result.rack_busy_hours < result.completion_time_hours * 20 * 0.2


def test_monte_carlo_returns_requested_trial_count():
    campaign, suites, inventory, licenses, policy = _abundant_racks_scarce_license_scenario()
    results = monte_carlo(campaign, suites, inventory, licenses, policy, trials=5)
    assert len(results) == 5
    assert all(r.completion_time_hours > 0 for r in results)
