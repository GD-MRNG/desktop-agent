from rich.console import Console
from rich.prompt import Confirm

_console = Console()


def request_approval(action: str, working_dir: str) -> bool:
    """Display a human-in-the-loop approval prompt and return the user's decision.

    Args:
        action: The shell command the agent wants to run.
        working_dir: Directory where the command would execute.

    Returns:
        True if the user approved, False if denied.
    """
    # Application-level safety gate — runs AFTER the agent decides to act.
    # Distinct from @input_guardrail which is SDK middleware running BEFORE the agent.
    # This gives the human final veto over any shell execution.
    _console.print(f"\n[bold yellow]⚠ APPROVAL REQUIRED[/bold yellow]")
    _console.print(f"  Command : [bold]{action}[/bold]")
    _console.print(f"  Cwd     : [dim]{working_dir}[/dim]")
    return Confirm.ask("  Allow?", default=False)
