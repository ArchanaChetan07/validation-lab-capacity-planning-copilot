import numpy as np

from capacity_copilot.models.test_suite import TestSuite, RegressionCampaign


def test_sample_runtime_positive_and_centered():
    suite = TestSuite(category="dft", mean_runtime_minutes=30)
    rng = np.random.default_rng(42)
    samples = suite.sample_runtime_hours(rng, n=2000)
    assert (samples > 0).all()
    # lognormal mean should be close to configured mean (within ~15%)
    assert abs(samples.mean() - 0.5) < 0.15


def test_compatible_rack_types_defaults_empty_set():
    suite = TestSuite(category="dsp", mean_runtime_minutes=10)
    assert suite.compatible_rack_types == set()


def test_campaign_total_tests():
    campaign = RegressionCampaign(suite_counts={"dft": 30000, "dsp": 20000})
    assert campaign.total_tests() == 50000
