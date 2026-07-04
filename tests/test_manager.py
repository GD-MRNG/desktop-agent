"""Tests for AgentManager orchestration: history accumulation, guardrail
tripwire handling, and trace correlation. Runner.run and trace() are patched so
these tests never make a live model call.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from agents import InputGuardrailTripwireTriggered

from agent.manager import AgentManager


def _fake_result(final_output: str, new_items=None, next_history=None):
    return SimpleNamespace(
        final_output=final_output,
        new_items=new_items or [],
        to_input_list=MagicMock(return_value=next_history or []),
    )


async def test_guardrail_tripwire_blocks_without_touching_history():
    manager = AgentManager()
    with patch("agent.manager.trace"), patch(
        "agent.manager.Runner.run",
        new=AsyncMock(side_effect=InputGuardrailTripwireTriggered(MagicMock())),
    ):
        response = await manager.run("rm -rf /")

    assert "[BLOCKED]" in response
    assert manager._history == []


async def test_run_accumulates_history_across_turns():
    manager = AgentManager()
    first_history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    second_history = first_history + [
        {"role": "user", "content": "again"},
        {"role": "assistant", "content": "still here"},
    ]

    with patch("agent.manager.trace"):
        with patch(
            "agent.manager.Runner.run",
            new=AsyncMock(return_value=_fake_result("hello", next_history=first_history)),
        ):
            response_1 = await manager.run("hi")
        with patch(
            "agent.manager.Runner.run",
            new=AsyncMock(return_value=_fake_result("still here", next_history=second_history)),
        ):
            response_2 = await manager.run("again")

    assert response_1 == "hello"
    assert response_2 == "still here"
    assert manager._history == second_history


async def test_run_passes_max_turns_and_session_group_id():
    manager = AgentManager()
    mock_trace = MagicMock()
    with patch("agent.manager.trace", return_value=mock_trace) as mock_trace_fn:
        with patch(
            "agent.manager.Runner.run", new=AsyncMock(return_value=_fake_result("ok"))
        ) as mock_run:
            await manager.run("hi")

    _, kwargs = mock_run.call_args
    assert kwargs["max_turns"] == 15

    _, trace_kwargs = mock_trace_fn.call_args
    assert trace_kwargs["group_id"] == manager._session_id


async def test_run_logs_tool_calls_from_new_items():
    from agents.items import ToolCallItem, ToolCallOutputItem

    tool_call = MagicMock(spec=ToolCallItem)
    tool_call.tool_name = "read_file"
    tool_call.raw_item = SimpleNamespace(arguments='{"path": "a.txt"}')

    tool_output = MagicMock(spec=ToolCallOutputItem)
    tool_output.output = "file contents"

    manager = AgentManager()
    with patch("agent.manager.trace"), patch(
        "agent.manager.Runner.run",
        new=AsyncMock(return_value=_fake_result("ok", new_items=[tool_call, tool_output])),
    ):
        with patch.object(manager._logger, "on_tool_call") as mock_on_call, patch.object(
            manager._logger, "on_tool_result"
        ) as mock_on_result:
            await manager.run("read a.txt")

    mock_on_call.assert_called_once_with("read_file", {"path": "a.txt"})
    mock_on_result.assert_called_once()
