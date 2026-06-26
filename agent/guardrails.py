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
    # [CONCEPT] Model routing by cost/capability: a cheap gpt-4o-mini handles the fast safety
    # check; the expensive gpt-4o reasoning agent never runs if the input is unsafe. The same
    # pattern applies when routing between providers — e.g. Claude for deep reasoning, Gemini
    # for fast classification — selecting the right model per task rather than using one model
    # for everything.
    #
    # @input_guardrail — SDK middleware running BEFORE the agent sees the message.
    # Contrast with agent/approvals.py, which is application-level safety AFTER the agent acts.
    result = await Runner.run(_guard_agent, input, context=ctx.context)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_safe,
    )
