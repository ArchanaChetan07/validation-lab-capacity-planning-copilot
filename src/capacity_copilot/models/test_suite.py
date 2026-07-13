"""Test-suite category domain model.

Each test-suite category has its own runtime distribution (tests within a
category are NOT uniform-duration), a required license (if any), and a set
of rack types it can run on.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class TestSuite:
    __test__ = False  # tell pytest this is not a test class despite the name

    category: str
    mean_runtime_minutes: float
    sigma: float = 0.4                      # lognormal shape parameter
    required_license: str | None = None
    compatible_rack_types: set[str] = None  # set at construction

    def __post_init__(self):
        if self.compatible_rack_types is None:
            self.compatible_rack_types = set()

    def sample_runtime_hours(self, rng: np.random.Generator, n: int = 1) -> np.ndarray:
        """Sample n runtimes (in hours) from this suite's lognormal distribution."""
        mean_h = self.mean_runtime_minutes / 60
        mu = np.log(mean_h) - (self.sigma ** 2) / 2
        return rng.lognormal(mean=mu, sigma=self.sigma, size=n)


@dataclass
class RegressionCampaign:
    """A concrete campaign: how many tests of each suite category to run."""
    suite_counts: dict[str, int]  # category -> test count

    def total_tests(self) -> int:
        return sum(self.suite_counts.values())
