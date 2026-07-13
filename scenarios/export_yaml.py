"""Export each synthetic scenario's key parameters + known ground truth as a
YAML file under scenarios/, for human review (Phase 5 deliverable format).
Source of truth remains scenarios/definitions.py; this is a doc export.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scenarios.definitions import build_scenarios  # noqa: E402


def scenario_to_dict(named) -> dict:
    spec = named.spec
    return {
        "name": named.name,
        "description": named.description,
        "known_ground_truth_bottleneck": named.known_bottleneck_prefix,
        "racks": {
            "count": len(spec.rack_inventory.racks),
            "type": spec.rack_inventory.racks[0].rack_type.value if spec.rack_inventory.racks else None,
        },
        "license_pools": {
            name: pool.total_seats for name, pool in spec.license_registry.pools.items()
        },
        "test_suites": {
            cat: {
                "mean_runtime_minutes": suite.mean_runtime_minutes,
                "required_license": suite.required_license,
            }
            for cat, suite in spec.suites.items()
        },
        "campaign_test_counts": spec.campaign.suite_counts,
        "total_tests": spec.campaign.total_tests(),
    }


def main():
    out_dir = Path(__file__).resolve().parent
    scenarios = build_scenarios()
    for named in scenarios:
        doc = scenario_to_dict(named)
        out_path = out_dir / f"{named.name}.yaml"
        with open(out_path, "w") as f:
            yaml.safe_dump(doc, f, sort_keys=False)
        print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
