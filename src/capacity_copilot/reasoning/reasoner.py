"""LLM explanation layer.

Architecturally constrained (NFR-2): the LLM is only ever given already-
computed simulation numbers and asked to explain/recommend — it is never
asked to estimate completion time or bottlenecks itself.
"""
from __future__ import annotations

import os

from anthropic import Anthropic, APIError, APIStatusError, APITimeoutError

_client: Anthropic | None = None


class ReasonerError(RuntimeError):
    """Raised when the LLM explanation call fails, after retries.
    Callers should catch this and return a clean error to the user rather
    than letting a raw Anthropic SDK exception (and stack trace) escape."""


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ReasonerError(
                "ANTHROPIC_API_KEY is not set. Set it as an environment variable "
                "(see .env.example) before calling /ask."
            )
        # explicit timeout + built-in retries: don't let one slow/flaky upstream
        # call hang a request indefinitely
        _client = Anthropic(api_key=api_key, timeout=20.0, max_retries=2)
    return _client


SYSTEM_PROMPT = """You are a validation-lab capacity-planning assistant.
You will be given ALREADY-COMPUTED simulation results (completion time,
utilization, and a bottleneck diagnosis from sensitivity analysis).

Rules:
- Only use the numbers given to you. Never invent or re-derive numbers.
- Explain what is binding the schedule and why, in plain terms.
- Give one concrete, quantified recommendation based on the given improvement_pct.
- Keep it under 150 words.
"""


def explain(
    scenario_summary: str,
    baseline_completion_hours: float,
    binding_constraint: str,
    perturbed_completion_hours: float,
    improvement_pct: float,
) -> str:
    user_content = f"""
Scenario: {scenario_summary}

Simulation results:
- Baseline P90 completion time: {baseline_completion_hours:.1f} hours
- Binding constraint identified by sensitivity analysis: {binding_constraint}
- If that constraint is relieved: completion time drops to
  {perturbed_completion_hours:.1f} hours ({improvement_pct:.1f}% improvement)

Explain the bottleneck and give one recommendation.
"""
    try:
        resp = _get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
    except ReasonerError:
        raise
    except APITimeoutError as e:
        raise ReasonerError("The explanation service timed out. Please try again.") from e
    except APIStatusError as e:
        raise ReasonerError(f"The explanation service returned an error (status {e.status_code}).") from e
    except APIError as e:
        raise ReasonerError("The explanation service is temporarily unavailable.") from e

    return "".join(block.text for block in resp.content if block.type == "text")

