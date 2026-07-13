"""Minimal NL -> structured scenario parser.

v1: regex/heuristic extraction. Good enough for the walking skeleton;
replace with an LLM-based extractor (via reasoner.py's client) later if
users type more free-form questions than this catches.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Bounds prevent two real failure modes:
#  - capacity=0 (rack_count or license_seats) crashes SimPy immediately (ValueError)
#  - very large test_count makes a single /ask request take minutes and get killed
#    by the hosting platform's request timeout (measured: 50k tests / 15 trials
#    took 151s; hosting platforms typically kill requests at 30-100s)
MIN_TEST_COUNT = 1
MAX_TEST_COUNT = 10_000
MIN_RACK_COUNT = 1
MAX_RACK_COUNT = 500
MIN_LICENSE_SEATS = 1
MAX_LICENSE_SEATS = 500
MIN_DEADLINE_HOURS = 0.1
MAX_DEADLINE_HOURS = 24 * 365  # 1 year
MIN_AVG_TEST_MINUTES = 0.01
MAX_AVG_TEST_MINUTES = 24 * 60  # 1 day per test


def _clamp(value: float, lo: float, hi: float, label: str, notes: list[str]) -> float:
    if value < lo:
        notes.append(f"{label} of {value:g} was below the supported minimum; using {lo:g}.")
        return lo
    if value > hi:
        notes.append(f"{label} of {value:g} exceeds what this demo can simulate quickly; using {hi:g}. "
                      f"For larger campaigns, run scripts/run_validation.py-style batch scenarios instead.")
        return hi
    return value


@dataclass
class ScenarioParams:
    test_count: int
    rack_count: int
    license_seats: int = 4          # default assumption if not stated
    deadline_hours: float = 96.0    # default: ~4 days if not stated
    avg_test_minutes: float = 12.0  # default average runtime per test
    notes: list[str] = field(default_factory=list)


def parse_query(text: str) -> ScenarioParams:
    test_count_match = re.search(r"([\d,]+)\s*(?:tests|regression tests|test cases)", text, re.I)
    rack_match = re.search(r"([\d,]+)\s*(?:racks|emulators|boards)", text, re.I)
    license_match = re.search(r"([\d,]+)\s*(?:license seats|licenses|seats)", text, re.I)
    hours_match = re.search(r"([\d.]+)\s*hours?", text, re.I)
    days_match = re.search(r"([\d.]+)\s*days?", text, re.I)

    def to_int(m, default):
        return int(m.group(1).replace(",", "")) if m else default

    test_count = to_int(test_count_match, 10_000)
    rack_count = to_int(rack_match, 8)
    license_seats = to_int(license_match, 4)

    if hours_match:
        deadline_hours = float(hours_match.group(1))
    elif days_match:
        deadline_hours = float(days_match.group(1)) * 24
    else:
        deadline_hours = 96.0

    notes: list[str] = []
    test_count = int(_clamp(test_count, MIN_TEST_COUNT, MAX_TEST_COUNT, "test count", notes))
    rack_count = int(_clamp(rack_count, MIN_RACK_COUNT, MAX_RACK_COUNT, "rack count", notes))
    license_seats = int(_clamp(license_seats, MIN_LICENSE_SEATS, MAX_LICENSE_SEATS, "license seat count", notes))
    deadline_hours = _clamp(deadline_hours, MIN_DEADLINE_HOURS, MAX_DEADLINE_HOURS, "deadline", notes)

    return ScenarioParams(
        test_count=test_count,
        rack_count=rack_count,
        license_seats=license_seats,
        deadline_hours=deadline_hours,
        notes=notes,
    )

