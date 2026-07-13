import json
from agents import Runner, trace, InputGuardrailTripwireTriggered
from agents.items import ToolCallItem, ToolCallOutputItem
from app_agents.desktop_agent import DesktopAgent
from agent.trace import TraceLogger
from rich.console import Console


class AgentManager:
    """Conductor — drives the Runner, owns conversation history, and logs the trace.

    Brain/Hands/Conductor separation: this class is the Conductor (the *when*).
    It knows nothing about how agents reason (Brain) or how tools execute (Hands).
    Swapping an agent or tool requires no changes here.
    """

    def __init__(self) -> None:
        # The Runner is stateless between calls. Conversation history must be
        # passed explicitly each turn via result.to_input_list(). This manager owns that state.
        self._history: list = []
        self._logger = TraceLogger()
        self._turn = 0

    async def run(self, user_input: str) -> str:
        """Run one agent turn and return the final response."""
        self._turn += 1
        self._logger.on_turn_start()

        # Build input: prior history + new user message
        input_payload = self._history + [{"role": "user", "content": user_input}]

        try:
            # trace() — SDK context manager grouping all events for this turn.
            # Sends structured data to OpenAI's tracing platform for debugging.
            with trace(f"desktop-agent-turn-{self._turn}"):
                # [CONCEPT] max_turns=15 — circuit breaker passed to the Runner, not the Agent.
                result = await Runner.run(DesktopAgent, input_payload, max_turns=15)
        except InputGuardrailTripwireTriggered:
            # @input_guardrail tripwire — the agent never ran; input was blocked.
            msg = "[BLOCKED] Safety guardrail prevented this request."
            self._logger.on_response(msg)
            return msg

        # Log tool calls and results from this turn for local CLI trace output.
        # new_items contains every RunItem produced during the turn.
        for item in result.new_items:
            if isinstance(item, ToolCallItem):
                raw = item.raw_item
                # raw_item is a ResponseFunctionToolCall for our tools/*.py function tools,
                # but hosted tools (e.g. WebSearchTool) produce a different raw type
                # (ResponseFunctionWebSearch) with no .name/.arguments — only .type/.action.
                args_str = getattr(raw, "arguments", None)
                if args_str:
                    try:
                        args = json.loads(args_str) if isinstance(args_str, str) else {}
                    except json.JSONDecodeError:
                        args = {"raw": args_str}
                else:
                    action = getattr(raw, "action", None)
                    args = action.model_dump() if action is not None else {}
                tool_name = item.tool_name or getattr(raw, "type", None) or "?"
                self._logger.on_tool_call(tool_name, args)
            elif isinstance(item, ToolCallOutputItem):
                self._logger.on_tool_result("result", str(item.output)[:200])

        # Persist history for the next turn
        self._history = result.to_input_list()

        response = str(result.final_output)
        self._logger.on_response(response)
        return response

    async def start(self) -> None:
        """Run the interactive CLI loop."""
        console = Console()
        console.print("[bold green]Desktop Agent ready. Type 'exit' to quit.[/bold green]\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Goodbye.[/dim]")
                break

            if user_input.lower() in {"exit", "quit", "bye"}:
                console.print("[dim]Goodbye.[/dim]")
                break
            if not user_input:
                continue

            await self.run(user_input)
