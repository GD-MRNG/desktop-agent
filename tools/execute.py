import asyncio
import platform
from agents import function_tool
from agent.approvals import request_approval
from schemas.models import CommandResult


@function_tool
async def run_command(command: str, working_dir: str = ".") -> CommandResult:
    """Run a shell command in the specified directory after user approval.

    Always pauses for explicit user confirmation before executing.
    The user can deny any command — the agent should respect that decision.

    Args:
        command: Shell command to execute.
        working_dir: Directory to run the command in. Defaults to current directory.
    """
    # [CONCEPT] Human-in-the-loop gate — explicit user confirmation before execution.
    # This is application-level safety, separate from the @input_guardrail middleware.
    # The agent decides to call this tool; the human decides whether it runs.
    approved = request_approval(command, working_dir)
    if not approved:
        return CommandResult(
            stdout="",
            stderr="Command denied by user.",
            exit_code=1,
            command=command,
        )

    # [CONCEPT] OS-aware shell routing — routes to the right shell per platform.
    if platform.system() == "Windows":
        shell_args = ["powershell", "-Command", command]
    else:
        shell_args = ["bash", "-c", command]

    proc = await asyncio.create_subprocess_exec(
        *shell_args,
        cwd=working_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_bytes, stderr_bytes = await proc.communicate()

    return CommandResult(
        stdout=stdout_bytes.decode("utf-8", errors="replace"),
        stderr=stderr_bytes.decode("utf-8", errors="replace"),
        exit_code=proc.returncode or 0,
        command=command,
    )
