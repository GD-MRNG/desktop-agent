import asyncio
import os
import platform
from agents import function_tool
from agent.approvals import request_approval
from schemas.models import CommandResult
from tools.sandbox import resolve_within_root

# Resource limits — no allow-list here on purpose. This is a general-purpose desktop
# agent; an allow-list would either be too broad to matter or too narrow to be useful.
# The guardrail (agent/guardrails.py) + human approval (agent/approvals.py) pair is the
# actual control; these caps just stop an approved-but-runaway command from hanging or
# flooding memory.
_DEFAULT_TIMEOUT_SECONDS = 60
_DEFAULT_MAX_OUTPUT_BYTES = 1_000_000


@function_tool
async def run_command(command: str, working_dir: str = ".") -> CommandResult:
    """Run a shell command in the specified directory after user approval.

    Always pauses for explicit user confirmation before executing.
    The user can deny any command — the agent should respect that decision.

    Args:
        command: Shell command to execute.
        working_dir: Directory to run the command in. Defaults to current directory.
    """
    # Human-in-the-loop gate — explicit user confirmation before execution.
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

    resolved_dir = resolve_within_root(working_dir)

    # OS-aware shell routing — routes to the right shell per platform.
    if platform.system() == "Windows":
        shell_args = ["powershell", "-Command", command]
    else:
        shell_args = ["bash", "-c", command]

    timeout = float(os.environ.get("AGENT_COMMAND_TIMEOUT_SECONDS", _DEFAULT_TIMEOUT_SECONDS))
    max_output = int(os.environ.get("AGENT_COMMAND_MAX_OUTPUT_BYTES", _DEFAULT_MAX_OUTPUT_BYTES))

    proc = await asyncio.create_subprocess_exec(
        *shell_args,
        cwd=resolved_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return CommandResult(
            stdout="",
            stderr=f"Command timed out after {timeout:.0f}s.",
            exit_code=124,  # matches the GNU `timeout` convention
            command=command,
        )

    def _decode_capped(raw: bytes) -> str:
        text = raw[:max_output].decode("utf-8", errors="replace")
        if len(raw) > max_output:
            text += "\n...[truncated]"
        return text

    return CommandResult(
        stdout=_decode_capped(stdout_bytes),
        stderr=_decode_capped(stderr_bytes),
        exit_code=proc.returncode or 0,
        command=command,
    )
