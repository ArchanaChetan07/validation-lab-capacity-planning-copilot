"""Priority tiering and preemption policy.

Lower tier number = higher priority (tier 0 preempts tier 1, etc.), mirroring
common scheduler conventions. Used by the sim engine to decide queue order
and whether an in-flight job gets bumped.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class PriorityTier(IntEnum):
    URGENT = 0       # e.g., tape-out-blocking hotfix regression
    STANDARD = 1     # normal regression campaign
    BACKGROUND = 2   # opportunistic / best-effort jobs


@dataclass
class PriorityPolicy:
    preemption_enabled: bool = True

    def can_preempt(self, incoming: PriorityTier, running: PriorityTier) -> bool:
        """Whether an incoming job of `incoming` tier may preempt a running job."""
        if not self.preemption_enabled:
            return False
        return incoming < running


@dataclass
class QueuedJob:
    suite_category: str
    tier: PriorityTier
    arrival_time: float = 0.0
