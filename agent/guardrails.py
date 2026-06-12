from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)
from schemas.models import SafetyCheck

_guard_agent = Agent(
    name="SafetyChecker",
    instructions="""Evaluate whether the user's request contains dangerous system operations.
Mark is_safe=False for: rm -rf, sudo rm, format disk, DROP TABLE, DELETE FROM,
mkfs, dd if=/dev/zero, shutdown, reboot, del /f /s /q, or any request to
mass-delete or corrupt data.
Mark is_safe=True for all normal file, search, web, and shell tasks.""",
    output_type=SafetyCheck,
    model="gpt-4o-mini",
)


@input_guardrail
async def safety_check(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    # @input_guardrail — SDK middleware running BEFORE the agent sees the message.
    # A cheap gpt-4o-mini model does the check; the main gpt-4o agent never runs if unsafe.
    # Contrast with agent/approvals.py, which is application-level safety AFTER the agent acts.
    result = await Runner.run(_guard_agent, input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_safe,
    )
