from agents import Agent

# [CONCEPT] agent.as_tool() pattern — this agent is registered as a callable tool on
# DesktopAgent. When called, DesktopAgent gets the summary result back and continues its
# own reasoning. Contrast with handoff, where the calling agent exits the flow entirely.
SummaryAgent = Agent(
    name="SummaryAgent",
    instructions="""Summarise the provided text concisely in 3–5 sentences.
Focus on key points; omit filler. Return only the summary, nothing else.""",
    model="gpt-4o",
)
# [CONCEPT] max_turns is a Runner-level circuit breaker, not an Agent property.
# It is set via as_tool(max_turns=3) in desktop_agent.py, constraining this sub-agent's loop.
