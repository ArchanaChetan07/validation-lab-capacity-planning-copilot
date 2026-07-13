"""Rack inventory domain model.

A Rack represents a single FPGA prototyping board or hardware emulator unit
in the lab. Racks are heterogeneous: not every rack can run every test suite.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RackType(str, Enum):
    FPGA_PROTOTYPE = "fpga_prototype"
    EMULATOR = "emulator"


class RackStatus(str, Enum):
    AVAILABLE = "available"
    DOWN = "down"
    RESERVED = "reserved"


@dataclass
class Rack:
    rack_id: str
    rack_type: RackType
    compatible_suites: set[str] = field(default_factory=set)
    status: RackStatus = RackStatus.AVAILABLE

    def can_run(self, suite_category: str) -> bool:
        """Whether this rack supports the given test-suite category."""
        return (
            self.status == RackStatus.AVAILABLE
            and suite_category in self.compatible_suites
        )


@dataclass
class RackInventory:
    racks: list[Rack]

    def available_for(self, suite_category: str) -> list[Rack]:
        return [r for r in self.racks if r.can_run(suite_category)]

    def total_count(self) -> int:
        return len(self.racks)

    def available_count(self) -> int:
        return sum(1 for r in self.racks if r.status == RackStatus.AVAILABLE)
