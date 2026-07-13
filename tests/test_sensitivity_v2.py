from capacity_copilot.models.rack import Rack, RackInventory, RackType
from capacity_copilot.models.license_pool import LicensePool, LicenseRegistry
from capacity_copilot.models.test_suite import TestSuite, RegressionCampaign
from capacity_copilot.models.priority_policy import PriorityPolicy
from capacity_copilot.models.scenario import ScenarioSpec
from capacity_copilot.analysis.sensitivity_v2 import diagnose


def _make_spec(rack_count, license_seats, suite_counts, mean_minutes=6):
    inventory = RackInventory(racks=[
        Rack(rack_id=f"r{i}", rack_type=RackType.FPGA_PROTOTYPE, compatible_suites={"dft"})
        for i in range(rack_count)
    ])
    license_registry = LicenseRegistry()
    license_registry.add(LicensePool(name="dft_tool", total_seats=license_seats))
    suites = {
        "dft": TestSuite(
            category="dft", mean_runtime_minutes=mean_minutes,
            required_license="dft_tool",
            compatible_rack_types={RackType.FPGA_PROTOTYPE.value},
        )
    }
    campaign = RegressionCampaign(suite_counts=suite_counts)
    return ScenarioSpec(campaign, suites, inventory, license_registry, PriorityPolicy())


def test_scenario_a_abundant_racks_scarce_license():
    """Known ground truth: license pool is the binding constraint."""
    spec = _make_spec(rack_count=20, license_seats=1, suite_counts={"dft": 30})
    report = diagnose(spec, trials=8)
    assert report.binding_constraint.startswith("license_seats")
    assert report.improvement_pct > 0


def test_scenario_b_abundant_everything_scarce_racks():
    """Known ground truth: with generous licenses but only 1 rack, rack count binds."""
    spec = _make_spec(rack_count=1, license_seats=20, suite_counts={"dft": 30})
    report = diagnose(spec, trials=8)
    assert report.binding_constraint.startswith("rack_count")
    assert report.improvement_pct > 0


def test_dominant_suite_category_identifies_the_slow_one():
    inventory = RackInventory(racks=[
        Rack(rack_id="r1", rack_type=RackType.FPGA_PROTOTYPE, compatible_suites={"dft", "dsp"})
    ])
    license_registry = LicenseRegistry()
    license_registry.add(LicensePool(name="tool", total_seats=5))
    suites = {
        "dft": TestSuite(category="dft", mean_runtime_minutes=5, required_license="tool",
                          compatible_rack_types={RackType.FPGA_PROTOTYPE.value}),
        "dsp": TestSuite(category="dsp", mean_runtime_minutes=120, required_license="tool",
                          compatible_rack_types={RackType.FPGA_PROTOTYPE.value}),
    }
    campaign = RegressionCampaign(suite_counts={"dft": 100, "dsp": 10})
    spec = ScenarioSpec(campaign, suites, inventory, license_registry, PriorityPolicy())
    # dsp: 10*120=1200 total-minutes vs dft: 100*5=500 -> dsp should dominate
    assert spec.dominant_suite_category() == "dsp"
