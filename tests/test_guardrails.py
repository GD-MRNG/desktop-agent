"""Tests for the @input_guardrail safety check.

Runner.run is patched rather than calling the real gpt-4o-mini classifier, so these
tests exercise the tripwire wiring without a live API call.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from agent.guardrails import safety_check
from schemas.models import SafetyCheck


async def test_safety_check_passes_safe_input():
    fake_result = SimpleNamespace(final_output=SafetyCheck(is_safe=True, reason="normal request"))
    with patch("agent.guardrails.Runner.run", new=AsyncMock(return_value=fake_result)):
        output = await safety_check.guardrail_function(
            ctx=SimpleNamespace(context=None), agent=None, input="list files"
        )
    assert output.tripwire_triggered is False
    assert output.output_info.is_safe is True


async def test_safety_check_trips_on_unsafe_input():
    fake_result = SimpleNamespace(
        final_output=SafetyCheck(is_safe=False, reason="destructive command")
    )
    with patch("agent.guardrails.Runner.run", new=AsyncMock(return_value=fake_result)):
        output = await safety_check.guardrail_function(
            ctx=SimpleNamespace(context=None), agent=None, input="rm -rf /"
        )
    assert output.tripwire_triggered is True
    assert output.output_info.is_safe is False
