"""License pool domain model.

Emulator/tool and IP-block simulation licenses are frequently scarcer than
the hardware itself. A LicensePool tracks seat counts per named license and
supports checking/holding/releasing seats.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LicensePool:
    name: str
    total_seats: int
    held_seats: int = 0

    def available(self) -> int:
        return self.total_seats - self.held_seats

    def can_hold(self, count: int = 1) -> bool:
        return self.available() >= count

    def hold(self, count: int = 1) -> None:
        if not self.can_hold(count):
            raise ValueError(
                f"Cannot hold {count} seat(s) of '{self.name}': "
                f"only {self.available()} available"
            )
        self.held_seats += count

    def release(self, count: int = 1) -> None:
        self.held_seats = max(0, self.held_seats - count)


@dataclass
class LicenseRegistry:
    """Collection of license pools, keyed by name."""
    pools: dict[str, LicensePool] = field(default_factory=dict)

    def add(self, pool: LicensePool) -> None:
        self.pools[pool.name] = pool

    def get(self, name: str) -> LicensePool:
        return self.pools[name]

    def can_hold(self, name: str, count: int = 1) -> bool:
        return self.pools[name].can_hold(count)

    def utilization(self, name: str) -> float:
        pool = self.pools[name]
        return pool.held_seats / pool.total_seats if pool.total_seats else 0.0
