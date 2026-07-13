from capacity_copilot.models.priority_policy import PriorityPolicy, PriorityTier


def test_urgent_preempts_standard():
    policy = PriorityPolicy(preemption_enabled=True)
    assert policy.can_preempt(PriorityTier.URGENT, PriorityTier.STANDARD) is True


def test_standard_cannot_preempt_urgent():
    policy = PriorityPolicy(preemption_enabled=True)
    assert policy.can_preempt(PriorityTier.STANDARD, PriorityTier.URGENT) is False


def test_preemption_disabled_blocks_everything():
    policy = PriorityPolicy(preemption_enabled=False)
    assert policy.can_preempt(PriorityTier.URGENT, PriorityTier.BACKGROUND) is False
