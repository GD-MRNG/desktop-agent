from rich.console import Console
from rich.rule import Rule


class TraceLogger:
    """Prints a visible reasoning trace to the console for each agent turn.

    Observability — makes the agent's internal state visible without
    needing an external tracing service. Every tool call and result is printed
    so the user can follow what the agent is doing and why.
    """

    def __init__(self) -> None:
        self._console = Console()

    def on_turn_start(self) -> None:
        self._console.print(Rule(style="dim"))

    def on_trace_started(self, trace_id: str) -> None:
        # Surfaces the dashboard link for this turn's trace so a developer can jump
        # straight from the CLI to platform.openai.com/traces while debugging.
        url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
        self._console.print(f"[dim][TRACE][/dim] {url}")

    def on_tool_call(self, name: str, args: dict) -> None:
        args_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
        self._console.print(f"[bold cyan][TOOL CALL][/bold cyan] {name}({args_str})")

    def on_tool_result(self, name: str, result: str) -> None:
        short = result[:120] + "…" if len(result) > 120 else result
        self._console.print(f"[bold green][TOOL RESULT][/bold green] {name}: {short}")

    def on_reasoning(self, text: str) -> None:
        self._console.print(f"[bold yellow][AGENT][/bold yellow] {text}")

    def on_response(self, text: str) -> None:
        self._console.print(Rule(style="dim"))
        self._console.print(f"[bold white][RESPONSE][/bold white] {text}")
        self._console.print(Rule(style="dim"))
